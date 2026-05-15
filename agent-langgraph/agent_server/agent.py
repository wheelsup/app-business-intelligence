import asyncio
import json
import logging
import os
from datetime import datetime
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

LLM_ENDPOINT_NAME        = os.getenv("LLM_ENDPOINT_NAME", "databricks-claude-opus-4-7")
GENIE_SPACE_ID           = os.getenv("GENIE_SPACE_ID", "01f148039e131b10b43b6f97295e52e7")
CONNECTED_TABLE          = os.getenv("CONNECTED_TABLE", "slf_srvc.test_db.reporting_flight")
VECTOR_SEARCH_INDEX_NAME = os.getenv("VECTOR_SEARCH_INDEX_NAME", "slf_srvc.test_db.vector_db_knowledge_index")

agent_logger = AgentLogger(workspace_client=sp_workspace_client)

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

    start = datetime.now()
    try:
        if conversation_id is None:
            message = w.genie.start_conversation_and_wait(GENIE_SPACE_ID, question)
        else:
            message = w.genie.create_message_and_wait(GENIE_SPACE_ID, conversation_id, question)
    except Exception as e:
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.error("Genie call failed: %s", e, exc_info=True)
        asyncio.create_task(agent_logger.log_tool_call(
            conversation_id=session_id, activity="Call Genie",
            tool_input=question, response="",
            duration_ms=duration_ms, status="error", error_message=str(e),
        ))
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

    result_json = {
        "text": result_text,
        "sql": result_sql,
        "dataframe_records": result_records,
        "conversation_id": new_conversation_id,
    }
    
    duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    asyncio.create_task(agent_logger.log_tool_call(
        conversation_id=session_id, activity="Call Genie",
        tool_input=question, response=result_text,
        duration_ms=duration_ms, status="success",
        raw_payload=json.dumps(result_json),
    ))

    return json.dumps(result_json)


@tool
def search_business_context(query: str) -> str:
    """Search the business context knowledge base for column definitions,
    business rules, glossary terms, and domain knowledge relevant to the query.
    Always call this BEFORE query_genie for any flight data question so that
    Genie receives enriched context and generates more accurate SQL.
    Returns matched context text with traceability IDs."""
    if not VECTOR_SEARCH_INDEX_NAME:
        return json.dumps({"context": "", "retrieved_ids": [], "similarity_scores": []})

    try:
        session_id = get_session_id(None) or "default"
    except Exception:
        session_id = "default"

    start = datetime.now()
    try:
        vs_index = sp_workspace_client.vector_search_indexes.get_index(VECTOR_SEARCH_INDEX_NAME)
        results = vs_index.similarity_search(
            query_text=query,
            columns=["id", "content", "category", "table_name"],
            num_results=3,
        )
        rows = results.get("result", {}).get("data_array", [])
        retrieved_ids    = [str(row[0]) for row in rows]   # column 0 = id
        context_pieces   = [str(row[1]) for row in rows]   # column 1 = content
        similarity_scores = results.get("result", {}).get("score", [])

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.info("vector_search retrieved ids=%s scores=%s", retrieved_ids, similarity_scores)

        asyncio.create_task(agent_logger.log_tool_call(
            conversation_id=session_id,
            activity="Call Vector DB",
            tool_input=query,
            response="\n".join(context_pieces)[:2000],
            duration_ms=duration_ms,
            status="success",
            raw_payload=json.dumps(results),
            retrieved_ids=json.dumps(retrieved_ids),
            similarity_scores=json.dumps(similarity_scores),
        ))
        return json.dumps({
            "context": "\n".join(context_pieces),
            "retrieved_ids": retrieved_ids,
            "similarity_scores": similarity_scores,
        })
    except Exception as e:
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.error("search_business_context failed: %s", e, exc_info=True)
        asyncio.create_task(agent_logger.log_tool_call(
            conversation_id=session_id,
            activity="Call Vector DB",
            tool_input=query,
            response="",
            duration_ms=duration_ms,
            status="error",
            error_message=str(e),
            retrieved_ids=json.dumps([]),
            similarity_scores=json.dumps([]),
        ))
        return json.dumps({"context": "", "retrieved_ids": [], "similarity_scores": []})


SYSTEM_PROMPT = (
    "You are a business intelligence assistant. "
    "When a user asks about flight data — such as row counts, aggregates, trends, "
    "specific records, 'show me…', 'how many…', 'what is the average…', or any "
    "question that can be answered from the table slf_srvc.test_db.reporting_flight — "
    "you MUST call the query_genie tool and base your answer on its response. "
    "When a user asks about policies, glossary terms, definitions, documentation, "
    "or knowledge-base content — such as 'what does X mean', 'what is the policy for…', "
    "or any lookup that requires unstructured reference material — you MUST use the "
    "vector search tool. "
    "Never invent or fabricate data; if neither tool is appropriate for the question, "
    "tell the user clearly that you cannot help with that request. "
    "Never execute SQL directly: all data access must go through query_genie or the "
    "vector search tool — never through databricks-sql-connector, spark.sql(), or any "
    "other direct database interface."
)


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time, search_business_context, query_genie]
    # search_business_context replaces MCP vector search — no mcp_client needed for vector DB
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
    
    # Extract user prompt from the last user message in request.input
    if request.input:
        for msg in reversed(request.input):
            if msg.role == "user":
                user_prompt = msg.content if isinstance(msg.content, str) else ""
                break
    
    if session_id != "unknown":
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

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
    total_tokens_used = None
    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"]),
        agent_logger=agent_logger,
        conversation_id=session_id,
    ):
        # Capture final response text from output events
        if event.type == "response.output_item.done" and event.item:
            if hasattr(event.item, "content"):
                final_response_text = event.item.content
        yield event

    # Log final response at end
    await agent_logger.log_final_response(
        conversation_id=session_id, user_id=user_id,
        orchestrator_model=LLM_ENDPOINT_NAME,
        response=final_response_text, status="success",
        total_tokens=total_tokens_used,
    )
