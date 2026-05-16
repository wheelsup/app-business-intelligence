import asyncio
import json
import logging
import os
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks
from langchain.agents import create_agent
from langchain_core.tools import tool
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.agent_logger import AgentLogger
from agent_server.tool_registry import load_tools
from agent_server.utils import (
    get_databricks_host_from_env,
    get_session_id,
    get_user_workspace_client,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
mlflow.langchain.autolog()
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)
sp_workspace_client = WorkspaceClient()

LLM_ENDPOINT_NAME = os.getenv("LLM_ENDPOINT_NAME", "databricks-claude-opus-4-7")

# Path to the YAML file that declares which tools the agent has. Tools are
# defined in tools.yaml at the repo root — see that file's header for the
# add-a-tool workflow.
TOOLS_CONFIG_PATH = Path(__file__).parent.parent / "tools.yaml"

agent_logger = AgentLogger(workspace_client=sp_workspace_client)

# Per-turn conversation ID, set by stream_handler at the start of each
# request. Tools read this via the resolver passed to load_tools() so they
# know which conversation to log under. ContextVars propagate through
# asyncio.to_thread, which is how LangChain runs sync tools — so the value
# set on the event-loop thread becomes visible inside the tool worker.
_current_session_id: ContextVar[str] = ContextVar(
    "current_session_id", default="default"
)


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


# Load all data-source tools once at startup from tools.yaml. Adding a new
# tool of an existing backend type = edit YAML + restart. Adding a new
# backend type = create agent_server/backends/<name>.py and register it in
# tool_registry.BACKEND_HANDLERS.
_LOADED_TOOLS = load_tools(
    config_path=TOOLS_CONFIG_PATH,
    agent_logger=agent_logger,
    workspace_client=sp_workspace_client,
    session_id_resolver=lambda: _current_session_id.get(),
)


SYSTEM_PROMPT = (
    "You are a business intelligence assistant for the company. "
    "You help employees by calling the appropriate tool from the toolset "
    "available to you. Each tool's description explains what data source it "
    "covers and when to use it — read those descriptions carefully and pick "
    "the most appropriate tool(s) for the user's question. Multiple tools "
    "may be relevant for one question; call them as needed and combine "
    "their results. "
    "If no available tool fits the question, tell the user clearly that "
    "you cannot help with that request — do NOT invent, guess, or "
    "fabricate data. "
    "Never bypass the tools by writing or executing SQL directly, calling "
    "external APIs, or accessing data systems outside the provided tools."
)


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    # get_current_time stays hardcoded since it's a trivial utility, not a
    # data-source tool. Everything else comes from tools.yaml.
    tools = [get_current_time, *_LOADED_TOOLS]
    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
    return create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    session_id = get_session_id(request) or "unknown"
    user_id = request.context.user_id if request.context else "unknown"
    user_prompt = ""  # extracted from last user message in request.input

    # Extract user prompt from the last user message in request.input.
    # request.input items are Pydantic objects of various Responses-API
    # subtypes; the safest path is to .model_dump() each one and inspect the
    # resulting dict. Content may be a string or a list of {type, text} items.
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    t = item.get("text") or item.get("content")
                    if isinstance(t, str):
                        parts.append(t)
                elif isinstance(item, str):
                    parts.append(item)
            return "".join(parts)
        if isinstance(content, dict):
            t = content.get("text") or content.get("content")
            return t if isinstance(t, str) else ""
        return ""

    if request.input:
        for msg in reversed(request.input):
            try:
                msg_dict = msg.model_dump() if hasattr(msg, "model_dump") else (
                    msg if isinstance(msg, dict) else {}
                )
            except Exception:
                msg_dict = {}
            if msg_dict.get("role") == "user":
                user_prompt = _extract_text(msg_dict.get("content"))
                if user_prompt:
                    break
    
    if session_id != "unknown":
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    # Make the session id visible to sync @tool functions (which run in
    # worker threads via LangChain's asyncio.to_thread). Setting on the
    # event-loop thread; the ContextVar value propagates across to_thread
    # automatically per Python's contextvars / asyncio semantics.
    _current_session_id.set(session_id)

    # Log user request at start
    await agent_logger.log_user_request(
        conversation_id=session_id, user_id=user_id,
        user_prompt=user_prompt, orchestrator_model=LLM_ENDPOINT_NAME,
    )

    # By default, uses service principal credentials.
    # For on-behalf-of user authentication, use get_user_workspace_client() instead:
    #   agent = await init_agent(workspace_client=get_user_workspace_client())
    agent = await init_agent()
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    final_response_text = ""
    final_status = "success"
    final_error: Optional[str] = None
    # Mutable dict that process_agent_astream_events fills with per-turn stats
    # (running total_tokens, last LLM Thinking chunk id for dedup, ...)
    turn_stats: Dict[str, Any] = {}
    try:
        async for event in process_agent_astream_events(
            agent.astream(input=messages, stream_mode=["updates", "messages"]),
            agent_logger=agent_logger,
            conversation_id=session_id,
            orchestrator_model=LLM_ENDPOINT_NAME,
            stats=turn_stats,
        ):
            # Accumulate the final response text from streamed delta events.
            # The Responses API streams the answer as many
            # `response.output_text.delta` events each carrying a `delta`
            # chunk. The `response.output_item.done` event arrives at the
            # end with `content=None` — the protocol expects the consumer
            # to reconstruct the full text from the deltas.
            etype = getattr(event, "type", "")
            if etype == "response.output_text.delta":
                ed: Dict[str, Any] = {}
                try:
                    if hasattr(event, "model_dump"):
                        ed = event.model_dump()
                except Exception:
                    ed = {}
                delta = ed.get("delta") if isinstance(ed, dict) else None
                if delta is None:
                    delta = getattr(event, "delta", None)
                if isinstance(delta, str):
                    final_response_text += delta
                elif isinstance(delta, dict):
                    t = delta.get("text")
                    if isinstance(t, str):
                        final_response_text += t
            yield event
    except Exception as e:
        final_status = "error"
        final_error = str(e)
        logger.exception("stream_handler failed: %s", e)
        raise
    finally:
        # Guarantee Final Response row even on early cancellation / exception
        await agent_logger.log_final_response(
            conversation_id=session_id, user_id=user_id,
            orchestrator_model=LLM_ENDPOINT_NAME,
            response=final_response_text, status=final_status,
            error_message=final_error,
            total_tokens=turn_stats.get("total_tokens"),
        )
