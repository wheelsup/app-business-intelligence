"""
Backend handlers for tool dispatch.

Each backend module exposes a single `call(question, *, params, session_id,
agent_logger, workspace_client)` function. See agent_server/tool_registry.py
for the dispatch wiring and tools.yaml for the tool definitions.
"""
