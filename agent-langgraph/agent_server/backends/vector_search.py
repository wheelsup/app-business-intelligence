"""
Vector Search backend — runs a similarity_search against a Databricks
Vector Search index and returns the top-N text chunks plus traceability
(retrieved chunk IDs + similarity scores).

Tool params (from tools.yaml):
    index_name (str, required)        Full UC name of the index.
    columns (list[str], optional)     Columns to fetch from the index.
                                      Defaults to ["chunk_id", "text"].
    num_results (int, optional)       Top-N. Defaults to 3.
    filters_json (str|dict, optional) JSON filter expression to scope the
                                      search to a subset of the index
                                      (e.g. '{"domain": "flights"}'). Used
                                      to keep one shared index but expose
                                      multiple per-domain search tools.
                                      Both string and dict accepted; a dict
                                      is JSON-stringified before sending.
    activity_label (str, optional)    Logging label. Defaults to
                                      "Call Vector DB".
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def call(
    question: str,
    *,
    params: dict,
    session_id: str,
    agent_logger,
    workspace_client,
) -> str:
    """Query the configured vector index, log the result (including
    retrieved_ids + similarity_scores for traceability), and return a JSON
    string the LLM can consume.
    """
    index_name = params.get("index_name")
    columns = params.get("columns") or ["chunk_id", "text"]
    num_results = int(params.get("num_results") or 3)
    activity_label = params.get("activity_label", "Call Vector DB")

    # Optional JSON filter — accept either a JSON string (from YAML) or a
    # dict (in case someone constructs params programmatically). The SDK
    # expects a string.
    raw_filters = params.get("filters_json")
    if raw_filters is None:
        filters_json = None
    elif isinstance(raw_filters, str):
        filters_json = raw_filters
    else:
        try:
            filters_json = json.dumps(raw_filters)
        except Exception:
            filters_json = None
    try:
        filters_payload = json.loads(filters_json) if filters_json else None
    except Exception:
        filters_payload = filters_json

    if not index_name:
        # Should not happen — tool_registry skips tools with missing required
        # env vars at startup. Defensive fallback.
        return json.dumps({
            "context": "", "retrieved_ids": [], "similarity_scores": [],
        })

    # Identify the "id-like" and "content-like" columns by position. We
    # request `columns` in the order given, so column 0 is treated as the
    # primary key and column 1 as the content/text. The API appends a
    # "score" column to whatever we requested, so we map score by name.
    id_col = columns[0] if columns else "chunk_id"
    content_col = columns[1] if len(columns) > 1 else "text"

    start = datetime.now()
    try:
        # Build kwargs so we only pass `filters_json` when set — the SDK
        # treats None as "no filter" if omitted but errors on some param
        # forms if explicitly None.
        query_kwargs = dict(
            index_name=index_name,
            columns=columns,
            query_text=question,
            num_results=num_results,
        )
        if filters_json:
            query_kwargs["filters_json"] = filters_json

        response = workspace_client.vector_search_indexes.query_index(**query_kwargs)

        col_names: list = []
        if response.manifest and response.manifest.columns:
            col_names = [c.name for c in response.manifest.columns]
        data_array = (
            response.result.data_array
            if (response.result and response.result.data_array)
            else []
        )
        id_idx = col_names.index(id_col) if id_col in col_names else 0
        content_idx = col_names.index(content_col) if content_col in col_names else 1
        score_idx = col_names.index("score") if "score" in col_names else -1

        retrieved_ids = [str(row[id_idx]) for row in data_array]
        context_pieces = [str(row[content_idx]) for row in data_array]
        similarity_scores = (
            [float(row[score_idx]) for row in data_array]
            if data_array and score_idx >= 0
            else []
        )

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.info(
            "vector_search retrieved ids=%s scores=%s",
            retrieved_ids, similarity_scores,
        )

        raw_payload = {
            "backend": "vector_search",
            "index_name": index_name,
            "query_text": question,
            "requested_columns": columns,
            "num_results": num_results,
            "filters": filters_payload,
            "retrieved_ids": retrieved_ids,
            "similarity_scores": similarity_scores,
            "response": response.as_dict(),
        }

        agent_logger.log_tool_call_threadsafe(
            conversation_id=session_id,
            activity=activity_label,
            tool_input=question,
            response="\n".join(context_pieces)[:2000],
            duration_ms=duration_ms,
            status="success",
            raw_payload=json.dumps(raw_payload),
            retrieved_ids=json.dumps(retrieved_ids),
            similarity_scores=json.dumps(similarity_scores),
        )
        return json.dumps({
            "context": "\n".join(context_pieces),
            "retrieved_ids": retrieved_ids,
            "similarity_scores": similarity_scores,
        })

    except Exception as e:
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        logger.error("vector_search failed: %s", e, exc_info=True)
        # Carry full error context on the row so debugging doesn't require
        # the backend log file.
        error_payload = json.dumps({
            "error": str(e),
            "error_type": type(e).__name__,
            "index_name": index_name,
            "requested_columns": columns,
            "query_text": question,
            "num_results": num_results,
            "filters": filters_payload,
        })
        agent_logger.log_tool_call_threadsafe(
            conversation_id=session_id,
            activity=activity_label,
            tool_input=question,
            response="",
            duration_ms=duration_ms,
            status="error",
            error_message=str(e),
            raw_payload=error_payload,
            retrieved_ids=json.dumps([]),
            similarity_scores=json.dumps([]),
        )
        return json.dumps({
            "context": "", "retrieved_ids": [], "similarity_scores": [],
        })
