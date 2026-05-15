# Agent Templates — Rules

Applies to `agent-*` directories (excluding `agent-langchain-ts`).

## Synced Files — Never Edit Directly

Shared files (`quickstart.py`, `start_app.py`, `evaluate_agent.py`, `preflight.py`, `deploy.yml`) are copied into each template. Always edit the source, then sync:

| Source | Sync command |
|---|---|
| `.scripts/source/` | `uv run python .scripts/sync-scripts.py` |
| `.claude/skills/` | `uv run python .scripts/sync-skills.py` |

Template-specific agent code (`{template}/agent_server/`) is edited directly — not synced.

## Per-template AGENTS.md

Each template has its own `{template}/AGENTS.md` (not synced). Contains template-specific guidance for end users.
