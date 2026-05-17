import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import uuid4

import mlflow
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from mlflow.genai.agent_server import get_invoke_function
from mlflow.types.responses import ResponsesAgentRequest

# Load environment variables from .env if it exists.
load_dotenv(dotenv_path=".env", override=True)
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)

# Import agent so the @invoke-registered function is available.
from agent_server import agent  # noqa: F401


WAREHOUSE_ID = os.getenv("DEBUG_WAREHOUSE_ID", "24062e246b5e17bf")
EVAL_CASES_TABLE = os.getenv(
    "AGENT_EVAL_CASES_TABLE", "slf_srvc.test_db.agent_eval_cases"
)
DEBUG_LOG_TABLE = os.getenv("DEBUG_LOG_TABLE", "slf_srvc.test_db.agent_debug_log")


@dataclass
class EvalCase:
    case_id: str
    question: str
    expected_tool_sequence: List[str]
    expected_retrieved_ids: List[str]
    expected_sql_contains: List[str]
    expected_facts: List[str]
    category: str
    difficulty: str


def _rows_from_statement_response(response: Any) -> List[List[Any]]:
    if not response or not getattr(response, "result", None):
        return []
    return getattr(response.result, "data_array", None) or []


def _execute_sql(workspace_client: WorkspaceClient, statement: str) -> List[List[Any]]:
    response = workspace_client.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=statement,
        wait_timeout="30s",
    )
    return _rows_from_statement_response(response)


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _array_sql(values: List[str]) -> str:
    if not values:
        return "array()"
    return "array(" + ", ".join(_sql_string(str(value)) for value in values) + ")"


def _parse_json(value: Any, default: Any) -> Any:
    if not value:
        return default
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _parse_array(value: Any) -> List[str]:
    parsed = _parse_json(value, value)
    if parsed is None:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _normalize_id(value: Any) -> str:
    text = str(value)
    if text.endswith(".0"):
        return text[:-2]
    return text


def _contains_expected_fact(response: str, fact: str) -> bool:
    response_lower = response.lower()
    fact_lower = fact.lower()
    if fact_lower in response_lower:
        return True
    if fact.isdigit():
        response_digits = re.sub(r"\D", "", response)
        return fact in response_digits
    return False


def _normalize_sql_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", "")).lower()


def load_eval_cases(workspace_client: WorkspaceClient) -> List[EvalCase]:
    rows = _execute_sql(
        workspace_client,
        f"""
        SELECT
          case_id,
          question,
          expected_tool_sequence,
          expected_retrieved_ids,
          expected_sql_contains,
          expected_facts,
          category,
          difficulty
        FROM {EVAL_CASES_TABLE}
        WHERE is_active = true
        ORDER BY case_id
        """,
    )
    return [
        EvalCase(
            case_id=str(row[0]),
            question=str(row[1]),
            expected_tool_sequence=_parse_array(row[2]),
            expected_retrieved_ids=_parse_array(row[3]),
            expected_sql_contains=_parse_array(row[4]),
            expected_facts=_parse_array(row[5]),
            category=str(row[6] or ""),
            difficulty=str(row[7] or ""),
        )
        for row in rows
    ]


def _tool_name_from_activity(activity: str) -> str | None:
    if activity == "Call Vector DB":
        return "search_flights_context"
    if activity == "Call Genie":
        return "query_flights_genie"
    return None


def _fetch_logs_for_conversation(
    workspace_client: WorkspaceClient, conversation_id: str
) -> List[Dict[str, Any]]:
    rows = _execute_sql(
        workspace_client,
        f"""
        SELECT
          activity,
          status,
          response,
          raw_payload,
          retrieved_ids,
          similarity_scores,
          trace_id,
          failure_category,
          logged_at
        FROM {DEBUG_LOG_TABLE}
        WHERE conversation_id = {_sql_string(conversation_id)}
        ORDER BY logged_at
        """,
    )
    return [
        {
            "activity": row[0],
            "status": row[1],
            "response": row[2],
            "raw_payload": row[3],
            "retrieved_ids": row[4],
            "similarity_scores": row[5],
            "trace_id": row[6],
            "failure_category": row[7],
            "logged_at": row[8],
        }
        for row in rows
    ]


def _wait_for_final_log(
    workspace_client: WorkspaceClient, conversation_id: str, timeout_seconds: int = 45
) -> List[Dict[str, Any]]:
    deadline = time.time() + timeout_seconds
    logs: List[Dict[str, Any]] = []
    while time.time() < deadline:
        logs = _fetch_logs_for_conversation(workspace_client, conversation_id)
        if any(row["activity"] == "Final Response" for row in logs):
            return logs
        time.sleep(2)
    return logs


def _score_case(case: EvalCase, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    tool_sequence = [
        tool
        for tool in (_tool_name_from_activity(str(row["activity"])) for row in logs)
        if tool
    ]
    actual_retrieved_ids: List[str] = []
    similarity_scores: List[float] = []
    genie_sql = ""
    final_response = ""

    for row in logs:
        if row["activity"] == "Call Vector DB":
            actual_retrieved_ids = [
                _normalize_id(value) for value in _parse_json(row["retrieved_ids"], [])
            ]
            similarity_scores = [
                float(value) for value in _parse_json(row["similarity_scores"], [])
            ]
        elif row["activity"] == "Call Genie":
            raw_payload = _parse_json(row["raw_payload"], {})
            genie_sql = str(raw_payload.get("sql") or "")
        elif row["activity"] == "Final Response":
            final_response = str(row["response"] or "")

    expected_prefix = case.expected_tool_sequence
    tool_sequence_pass = tool_sequence[: len(expected_prefix)] == expected_prefix
    expected_retrieved_ids = [_normalize_id(value) for value in case.expected_retrieved_ids]
    retrieved_overlap = sorted(set(expected_retrieved_ids) & set(actual_retrieved_ids))
    retrieval_pass = (
        not expected_retrieved_ids or len(retrieved_overlap) > 0
    )
    normalized_sql = _normalize_sql_text(genie_sql)
    sql_pass = all(
        _normalize_sql_text(snippet) in normalized_sql
        for snippet in case.expected_sql_contains
    )
    facts_pass = all(
        _contains_expected_fact(final_response, fact)
        for fact in case.expected_facts
    )
    final_success = any(
        row["activity"] == "Final Response" and row["status"] == "success"
        for row in logs
    )

    passed = all(
        [tool_sequence_pass, retrieval_pass, sql_pass, facts_pass, final_success]
    )
    return {
        "case_id": case.case_id,
        "question": case.question,
        "category": case.category,
        "difficulty": case.difficulty,
        "passed": passed,
        "tool_sequence_pass": tool_sequence_pass,
        "retrieval_pass": retrieval_pass,
        "sql_pass": sql_pass,
        "facts_pass": facts_pass,
        "final_success": final_success,
        "expected_tool_sequence": case.expected_tool_sequence,
        "actual_tool_sequence": tool_sequence,
        "expected_retrieved_ids": expected_retrieved_ids,
        "actual_retrieved_ids": actual_retrieved_ids,
        "retrieved_overlap": retrieved_overlap,
        "similarity_scores": similarity_scores,
        "genie_sql": genie_sql,
        "final_response": final_response,
        "trace_ids": sorted(
            {
                str(row["trace_id"])
                for row in logs
                if row.get("trace_id") not in (None, "")
            }
        ),
        "failure_categories": sorted(
            {
                str(row["failure_category"])
                for row in logs
                if row.get("failure_category") not in (None, "")
            }
        ),
    }


def _invoke_agent(case: EvalCase, invoke_fn: Any, conversation_id: str) -> Dict[str, Any]:
    request = ResponsesAgentRequest(
        input=[
            {
                "role": "user",
                "content": case.question,
            }
        ],
        custom_inputs={"session_id": conversation_id},
    )
    if asyncio.iscoroutinefunction(invoke_fn):
        return asyncio.run(invoke_fn(request)).model_dump()
    return invoke_fn(request).model_dump()


def evaluate() -> Dict[str, Any]:
    workspace_client = WorkspaceClient()
    cases = load_eval_cases(workspace_client)
    if not cases:
        raise RuntimeError(
            f"No active eval cases found in {EVAL_CASES_TABLE}. Populate the table first."
        )

    invoke_fn = get_invoke_function()
    if invoke_fn is None:
        raise RuntimeError("No @invoke function found. Import agent_server.agent first.")

    results: List[Dict[str, Any]] = []
    with mlflow.start_run(run_name="agent_eval_cases"):
        for case in cases:
            conversation_id = f"eval-{case.case_id}-{uuid4().hex[:8]}"
            try:
                _invoke_agent(case, invoke_fn, conversation_id)
            except Exception as exc:
                results.append(
                    {
                        "case_id": case.case_id,
                        "question": case.question,
                        "passed": False,
                        "error": str(exc),
                    }
                )
                continue

            logs = _wait_for_final_log(workspace_client, conversation_id)
            results.append(_score_case(case, logs))

        total = len(results)
        passed = sum(1 for result in results if result.get("passed"))
        mlflow.log_metric("eval_cases_total", total)
        mlflow.log_metric("eval_cases_passed", passed)
        mlflow.log_metric("eval_cases_pass_rate", passed / total if total else 0.0)
        mlflow.log_dict({"results": results}, "agent_eval_results.json")

    return {"total": len(results), "passed": passed, "results": results}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, default=str))
