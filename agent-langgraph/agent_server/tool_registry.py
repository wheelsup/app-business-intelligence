"""
Tool registry — loads agent tools from tools.yaml at startup, substitutes
${ENV_VAR} references, and builds a list of langchain @tool callables that
dispatch to the appropriate backend handler.

Adding a new BACKEND TYPE: import its `call` function and register it in
BACKEND_HANDLERS below. Then drop YAML entries with that backend name.

Adding a new TOOL of an existing backend: just add a YAML entry. No code
change needed.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml
from langchain_core.tools import StructuredTool

from agent_server.backends import genie as backend_genie
from agent_server.backends import stub as backend_stub
from agent_server.backends import vector_search as backend_vector_search

logger = logging.getLogger(__name__)


# Map of `backend:` value in YAML → handler function. Each handler has the
# signature: call(question, *, params, session_id, agent_logger, workspace_client) -> str
BACKEND_HANDLERS: Dict[str, Callable[..., str]] = {
    "genie": backend_genie.call,
    "vector_search": backend_vector_search.call,
    "stub": backend_stub.call,
    # Add new backends here, e.g.:
    # "powerbi": backend_powerbi.call,
    # "sharepoint": backend_sharepoint.call,
}


# Pattern matching ${VAR_NAME} in YAML param values
_ENV_VAR_PATTERN = re.compile(r"^\$\{([A-Z_][A-Z0-9_]*)\}$")


def _substitute_env(value: Any) -> Any:
    """Recursively substitute ${ENV_VAR} references in YAML values.

    Returns:
        The substituted value. If a referenced env var is unset OR resolves
        to an empty string, returns None (so the loader can detect missing
        config and skip the tool with a warning).
    """
    if isinstance(value, str):
        match = _ENV_VAR_PATTERN.match(value.strip())
        if match:
            env_name = match.group(1)
            resolved = os.environ.get(env_name, "")
            if not resolved:
                return None  # signal "missing"
            return resolved
        return value
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    return value


def _missing_keys(params: Dict[str, Any]) -> List[str]:
    """Return keys whose value resolved to None (i.e. ${VAR} that wasn't
    set in the environment)."""
    return [k for k, v in params.items() if v is None]


def load_tools(
    *,
    config_path: Path,
    agent_logger,
    workspace_client,
    session_id_resolver: Callable[[], str],
) -> List[StructuredTool]:
    """Read tools.yaml, resolve env vars, and return a list of langchain
    StructuredTool objects ready to pass to create_agent(tools=...).

    Args:
        config_path: path to tools.yaml.
        agent_logger: AgentLogger instance shared with the rest of the app.
        workspace_client: Databricks WorkspaceClient.
        session_id_resolver: zero-arg callable returning the current session
            id. Typically `lambda: _current_session_id.get()` from agent.py.
    """
    if not config_path.exists():
        logger.warning(
            "tool_registry: %s does not exist — no tools will be loaded",
            config_path,
        )
        return []

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    raw_tools = config.get("tools") or []
    if not isinstance(raw_tools, list):
        logger.warning("tool_registry: tools.yaml `tools:` key is not a list")
        return []

    loaded: List[StructuredTool] = []
    for spec in raw_tools:
        if not isinstance(spec, dict):
            logger.warning("tool_registry: skipping non-dict tool entry: %r", spec)
            continue

        name = spec.get("name")
        backend_name = spec.get("backend")
        description = spec.get("description") or ""
        raw_params = spec.get("params") or {}

        if not name or not backend_name:
            logger.warning(
                "tool_registry: skipping entry missing name or backend: %r", spec
            )
            continue

        handler = BACKEND_HANDLERS.get(backend_name)
        if handler is None:
            logger.warning(
                "tool_registry: skipping tool '%s' — unknown backend '%s'. "
                "Register it in agent_server/tool_registry.BACKEND_HANDLERS.",
                name, backend_name,
            )
            continue

        # Substitute env vars in params; skip the tool if any required ${VAR}
        # is missing — this lets you commit YAML entries before the matching
        # env var exists, without crashing the backend at startup.
        resolved_params = _substitute_env(raw_params) or {}
        missing = _missing_keys(resolved_params)
        if missing:
            logger.warning(
                "tool_registry: skipping tool '%s' — missing env vars for params: %s",
                name, missing,
            )
            continue

        loaded.append(
            _build_structured_tool(
                name=name,
                description=description.strip(),
                handler=handler,
                params=resolved_params,
                agent_logger=agent_logger,
                workspace_client=workspace_client,
                session_id_resolver=session_id_resolver,
            )
        )
        logger.info("tool_registry: loaded tool '%s' (backend=%s)", name, backend_name)

    logger.info("tool_registry: %d tool(s) loaded from %s", len(loaded), config_path)
    return loaded


def _build_structured_tool(
    *,
    name: str,
    description: str,
    handler: Callable[..., str],
    params: Dict[str, Any],
    agent_logger,
    workspace_client,
    session_id_resolver: Callable[[], str],
) -> StructuredTool:
    """Wrap a backend handler in a langchain StructuredTool.

    The returned tool exposes a single string arg (`question`) to the LLM
    and binds all the dependencies the handler needs via closure.
    """

    def _tool_fn(question: str) -> str:
        try:
            session_id = session_id_resolver()
        except Exception:
            session_id = "default"
        return handler(
            question,
            params=params,
            session_id=session_id,
            agent_logger=agent_logger,
            workspace_client=workspace_client,
        )

    # description shown to the LLM is what the loader extracted from YAML
    return StructuredTool.from_function(
        func=_tool_fn,
        name=name,
        description=description,
    )
