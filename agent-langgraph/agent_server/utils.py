import asyncio
import logging
from typing import Any, AsyncGenerator, AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from databricks_langchain.chat_models import json
from langchain.messages import AIMessageChunk, ToolMessage
from mlflow.genai.agent_server import get_request_headers
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentStreamEvent,
    create_text_delta,
    output_to_responses_items_stream,
)


def get_session_id(request: ResponsesAgentRequest) -> str | None:
    if request.context and request.context.conversation_id:
        return request.context.conversation_id
    if request.custom_inputs and isinstance(request.custom_inputs, dict):
        return request.custom_inputs.get("session_id")
    return None


def get_user_workspace_client() -> WorkspaceClient:
    token = get_request_headers().get("x-forwarded-access-token")
    return WorkspaceClient(token=token, auth_type="pat")


def get_databricks_host_from_env() -> Optional[str]:
    try:
        w = WorkspaceClient()
        return w.config.host
    except Exception as e:
        logging.exception(f"Error getting databricks host from env: {e}")
        return None


async def process_agent_astream_events(
    async_stream: AsyncIterator[Any],
    agent_logger=None,
    conversation_id: Optional[str] = None,
    orchestrator_model: str = "",
    stats: Optional[dict] = None,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """
    Generic helper to process agent stream events and yield ResponsesAgentStreamEvent objects.

    Args:
        async_stream: The async iterator from agent.astream()
        agent_logger: Optional AgentLogger instance for logging LLM thinking
        conversation_id: Optional conversation ID for logging context
        orchestrator_model: LLM endpoint name to attach to LLM Thinking rows
        stats: Optional mutable dict the caller can read after iteration to
            collect per-turn stats. Keys written:
              - "total_tokens": running sum across deduped LLM completions
              - "last_thinking_chunk_id": chunk.id of the last LLM Thinking
                row we logged (used to dedup duplicate final chunks)
    """
    # Local fallback if caller did not provide a stats dict
    if stats is None:
        stats = {}
    async for event in async_stream:
        if event[0] == "updates":
            for node_data in event[1].values():
                if len(node_data.get("messages", [])) > 0:
                    for msg in node_data["messages"]:
                        if isinstance(msg, ToolMessage) and not isinstance(msg.content, str):
                            msg.content = json.dumps(msg.content)
                    for item in output_to_responses_items_stream(node_data["messages"]):
                        yield item
        elif event[0] == "messages":
            try:
                chunk = event[1][0]
                if isinstance(chunk, AIMessageChunk):
                    # Fire LLM Thinking log ONLY when the chunk carries a real
                    # usage count. usage_metadata is present on every chunk
                    # as a dict, but intermediate chunks have total_tokens=0;
                    # only the final chunk of each LLM call has total_tokens>0.
                    # We ALSO dedup by chunk.id because LangChain (with
                    # stream_mode=['updates','messages']) tends to emit the
                    # final chunk twice — once as the streaming-mode chunk
                    # and once mirrored through the updates-mode aggregation.
                    if agent_logger:
                        usage = getattr(chunk, "usage_metadata", None)
                        total_tokens = None
                        if isinstance(usage, dict):
                            total_tokens = usage.get("total_tokens")
                        if total_tokens and total_tokens > 0:
                            chunk_id = getattr(chunk, "id", None)
                            if chunk_id != stats.get("last_thinking_chunk_id"):
                                stats["last_thinking_chunk_id"] = chunk_id
                                stats["total_tokens"] = (
                                    (stats.get("total_tokens") or 0) + total_tokens
                                )
                                asyncio.create_task(
                                    agent_logger.log_llm_thinking(
                                        conversation_id=conversation_id,
                                        orchestrator_model=orchestrator_model,
                                        total_tokens=total_tokens,
                                    )
                                )
                    # Stream text deltas to the client (unchanged behavior)
                    if (content := chunk.content):
                        yield ResponsesAgentStreamEvent(
                            **create_text_delta(delta=content, item_id=chunk.id)
                        )
            except Exception as e:
                logging.exception(f"Error processing agent stream event: {e}")
