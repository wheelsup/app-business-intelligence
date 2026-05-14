import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks, DatabricksMCPServer, DatabricksMultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.tools import tool
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

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

LLM_ENDPOINT_NAME     = os.getenv("LLM_ENDPOINT_NAME", "databricks-claude-opus-4-7")
GENIE_SPACE_ID        = os.getenv("GENIE_SPACE_ID", "01f148039e131b10b43b6f97295e52e7")
CONNECTED_TABLE       = os.getenv("CONNECTED_TABLE", "slf_srvc.test_db.reporting_flight")
VECTOR_SEARCH_MCP_URL = os.getenv("VECTOR_SEARCH_MCP_URL", "")


_genie_conversation_cache: Dict[str, str] = {}


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


@tool
def query_genie(question: str) -> str:
    """Query the Genie space for flight data questions against
    slf_srvc.test_db.reporting_flight. Use for: row counts,
    aggregates, "show me…", "how many…" type questions.
    Returns a JSON string with text, sql, dataframe_records, conversation_id.
    """
    from mlflow.types.responses import ResponsesAgentRequest  # local import to avoid circular

    # Resolve session id — fall back to a fixed key so the cache still works
    # when called outside a full request context (e.g. unit tests).
    try:
        session_id = get_session_id(None) or "default"
    except Exception:
        session_id = "default"

    w = sp_workspace_client
    conversation_id = _genie_conversation_cache.get(session_id)

    try:
        if conversation_id is None:
            message = w.genie.start_conversation_and_wait(GENIE_SPACE_ID, question)
        else:
            message = w.genie.create_message_and_wait(GENIE_SPACE_ID, conversation_id, question)
    except Exception as e:
        logger.error("Genie call failed: %s", e, exc_info=True)
        return json.dumps({"text": f"Genie error: {e}", "sql": "", "dataframe_records": [], "conversation_id": ""})

    # Persist conversation id for subsequent turns in this session
    new_conversation_id = getattr(message, "conversation_id", None) or conversation_id or ""
    if new_conversation_id:
        _genie_conversation_cache[session_id] = new_conversation_id

    message_id = getattr(message, "message_id", None) or getattr(message, "id", None)
    attachments = getattr(message, "attachments", None)

    result_text = ""
    result_sql = ""
    result_records: list = []

    if attachments:
        for att in attachments:
            text_obj = getattr(att, "text", None)
            if text_obj and getattr(text_obj, "content", None):
                result_text = text_obj.content

            query_obj = getattr(att, "query", None)
            if query_obj is not None:
                sql_str = (
                    getattr(query_obj, "query", None)
                    or getattr(query_obj, "statement", None)
                    or getattr(query_obj, "sql", None)
                    or getattr(query_obj, "query_text", None)
                )
                if sql_str:
                    result_sql = sql_str

                attachment_id = (
                    getattr(att, "attachment_id", None)
                    or getattr(att, "id", None)
                )
                if attachment_id and message_id and new_conversation_id:
                    try:
                        query_result = None
                        try:
                            query_result = w.genie.get_message_attachment_query_result(
                                space_id=GENIE_SPACE_ID,
                                conversation_id=new_conversation_id,
                                message_id=message_id,
                                attachment_id=attachment_id,
                            )
                        except AttributeError:
                            query_result = w.genie.get_message_query_result(
                                space_id=GENIE_SPACE_ID,
                                conversation_id=new_conversation_id,
                                message_id=message_id,
                            )

                        if query_result:
                            sr = getattr(query_result, "statement_response", None)
                            if sr and sr.result and sr.manifest:
                                rows = sr.result.data_array or []
                                cols = [c.name for c in sr.manifest.schema.columns]
                                result_records = [dict(zip(cols, row)) for row in rows]
                    except Exception as fe:
                        logger.warning("Failed to fetch query result: %s", fe, exc_info=True)

    if not result_text and getattr(message, "content", None):
        result_text = message.content
    if not result_text and not result_records:
        result_text = "I wasn't able to generate an answer. Please try rephrasing your question."

    return json.dumps({
        "text": result_text,
        "sql": result_sql,
        "dataframe_records": result_records,
        "conversation_id": new_conversation_id,
    })


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    return DatabricksMultiServerMCPClient(
        [
            DatabricksMCPServer(
                name="system-ai",
                url=f"{host_name}/api/2.0/mcp/functions/system/ai",
                workspace_client=workspace_client,
            ),
        ]
    )


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time]
    # To use MCP server tools instead, replace the line above with:
    #   mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
    #   try:
    #       tools.extend(await mcp_client.get_tools())
    #   except Exception:
    #       logger.warning("Failed to fetch MCP tools. Continuing without MCP tools.", exc_info=True)
    return create_agent(tools=tools, model=ChatDatabricks(endpoint="databricks-gpt-5-2"))


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
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    # By default, uses service principal credentials.
    # For on-behalf-of user authentication, use get_user_workspace_client() instead:
    #   agent = await init_agent(workspace_client=get_user_workspace_client())
    agent = await init_agent()
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"])
    ):
        yield event
