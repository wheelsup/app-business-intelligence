"""
Genie backend — answers natural-language questions against a Databricks
Genie space, returning text + SQL + dataframe rows.

Tool params (from tools.yaml):
    space_id (str, required)        Databricks Genie space ID.
    activity_label (str, optional)  Logging label. Defaults to "Call Genie".
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

# Conversation cache: maps (space_id, session_id) → genie conversation_id so
# follow-up turns within the same session preserve Genie context. Keying on
# space_id as well as session_id keeps multiple Genie tools (flights,
# finance, ...) from clobbering each other's conversation state.
_genie_conversation_cache: Dict[Tuple[str, str], str] = {}


def call(
    question: str,
    *,
    params: dict,
    session_id: str,
    agent_logger,
    workspace_client,
) -> str:
    """Forward `question` to the configured Genie space, log the result, and
    return a JSON string the LLM can consume.
    """
    space_id = params.get("space_id")
    activity_label = params.get("activity_label", "Call Genie")

    if not space_id:
        # Should not happen — tool_registry skips tools with missing required
        # env vars at startup. Defensive.
        return json.dumps({
            "text": "Genie tool is misconfigured (missing space_id).",
            "sql": "", "dataframe_records": [], "conversation_id": "",
        })

    cache_key = (space_id, session_id)
    conversation_id = _genie_conversation_cache.get(cache_key)
    w = workspace_client

    start = datetime.now()
    try:
        if conversation_id is None:
            message = w.genie.start_conversation_and_wait(space_id, question)
        else:
            message = w.genie.create_message_and_wait(
                space_id, conversation_id, question
            )
    except Exception as e:
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.error("Genie call failed: %s", e, exc_info=True)
        agent_logger.log_tool_call_threadsafe(
            conversation_id=session_id,
            activity=activity_label,
            tool_input=question,
            response="",
            duration_ms=duration_ms,
            status="error",
            error_message=str(e),
        )
        return json.dumps({
            "text": f"Genie error: {e}",
            "sql": "", "dataframe_records": [], "conversation_id": "",
        })

    # Persist the Genie conversation id so follow-up turns reuse context.
    new_conversation_id = (
        getattr(message, "conversation_id", None) or conversation_id or ""
    )
    if new_conversation_id:
        _genie_conversation_cache[cache_key] = new_conversation_id

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
                        try:
                            query_result = w.genie.get_message_attachment_query_result(
                                space_id=space_id,
                                conversation_id=new_conversation_id,
                                message_id=message_id,
                                attachment_id=attachment_id,
                            )
                        except AttributeError:
                            query_result = w.genie.get_message_query_result(
                                space_id=space_id,
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
        result_text = (
            "I wasn't able to generate an answer. Please try rephrasing your question."
        )

    result_json: Dict[str, Any] = {
        "text": result_text,
        "sql": result_sql,
        "dataframe_records": result_records,
        "conversation_id": new_conversation_id,
    }

    duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    agent_logger.log_tool_call_threadsafe(
        conversation_id=session_id,
        activity=activity_label,
        tool_input=question,
        response=result_text,
        duration_ms=duration_ms,
        status="success",
        raw_payload=json.dumps(result_json),
    )

    return json.dumps(result_json)
