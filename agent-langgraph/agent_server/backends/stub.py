"""
Stub backend — placeholder for tools whose real backend isn't wired up yet
(e.g., Power BI, SharePoint, Salesforce). Lets you draft the YAML tool
entry first; the LLM sees the tool, but any call returns a polite
"not implemented" message.

When you're ready to wire the real thing:
    1. Create agent_server/backends/<name>.py with a `call(...)` function.
    2. Register it in agent_server/tool_registry.BACKEND_HANDLERS.
    3. Flip `backend: stub` → `backend: <name>` in tools.yaml.
"""
from __future__ import annotations

import json
from datetime import datetime


def call(
    question: str,
    *,
    params: dict,
    session_id: str,
    agent_logger,
    workspace_client,  # unused, kept for signature parity
) -> str:
    activity_label = params.get("activity_label", "Call Stub")
    msg = (
        "This data source is configured in tools.yaml but its backend "
        "implementation isn't available yet. The administrator needs to "
        "wire the matching backend module before this question can be "
        "answered."
    )
    agent_logger.log_tool_call_threadsafe(
        conversation_id=session_id,
        activity=activity_label,
        tool_input=question,
        response=msg,
        duration_ms=0,
        status="error",
        error_message="stub backend — not yet implemented",
        raw_payload=json.dumps({
            "stub": True,
            "question": question,
            "params": params,
            "logged_at": datetime.utcnow().isoformat(),
        }),
    )
    return json.dumps({"text": msg, "stub": True})
