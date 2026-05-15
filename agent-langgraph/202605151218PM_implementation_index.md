# Implementation Plan — Phase 2 Index

Phase 1 is **done**. `agent_server/agent.py` already has:

- `get_current_time` tool
- `query_genie` tool (full Genie API path: `start_conversation_and_wait` → `create_message_and_wait` → `get_message_attachment_query_result`, with per-session `conversation_id` cache)
- An optional `DatabricksMultiServerMCPClient` Vector Search wiring guarded by the `VECTOR_SEARCH_MCP_URL` env var
- `SYSTEM_PROMPT` that already mentions a "vector search tool" for policy / glossary / definition lookups

What Phase 2 adds: a **hard-coded RAG tool** named `search_business_context`, backed by a Databricks Vector Search index built on top of the `slf_srvc.test_db.vector_db_knowledge` table. This replaces the optional MCP path with an in-process `@tool` so the agent always has a working RAG tool — no MCP server required, no env-var-conditional registration.

After Phase 2 the agent has exactly **three tools**:

1. `get_current_time` — clock
2. `query_genie` — structured flight data (Genie space → `reporting_flight`)
3. `search_business_context` — unstructured policy / glossary / definitions (Vector Search index → `vector_db_knowledge`)

All data access still routes through Databricks-governed surfaces. No direct SQL, no `databricks-sql-connector`, no `spark.sql()` exposed to the agent — this preserves the global Data Access Architecture rule.

## The 4 files

| File | Title | Code changes? | Depends on |
|---|---|---|---|
| `202605151218PM_implementation_part0.md` | Audit `vector_db_knowledge` table + Vector Search prerequisites | No | — |
| `202605151218PM_implementation_part1.md` | Create the Vector Search endpoint + index over `vector_db_knowledge` | No (Databricks-side) | Part 0 |
| `202605151218PM_implementation_part2.md` | Add `search_business_context` tool to `agent.py` | Yes | Part 1 |
| `202605151218PM_implementation_part3.md` | Update `SYSTEM_PROMPT`, finalize routing, remove dead MCP wiring | Yes | Part 2 |

## Architecture (after Phase 2)

```
                       ┌─────────────────────────────────────┐
                       │              User                   │
                       │    (Streamlit / Databricks App)     │
                       └──────────────────┬──────────────────┘
                                          │ ResponsesAgentRequest
                                          ▼
                       ┌─────────────────────────────────────┐
                       │         LangGraph Agent             │
                       │   ChatDatabricks(claude-opus-4-7)   │
                       │      + SYSTEM_PROMPT (router)       │
                       └──┬──────────────┬──────────────┬────┘
                          │              │              │
         ┌────────────────┘              │              └────────────────┐
         ▼                               ▼                               ▼
┌────────────────────┐       ┌────────────────────────┐      ┌────────────────────┐
│   query_genie      │       │  search_business_context │      │  get_current_time  │
│   (@tool)          │       │  (@tool)                │      │  (@tool)           │
└─────────┬──────────┘       └──────────┬──────────────┘      └────────────────────┘
          │ WorkspaceClient.genie       │ VectorSearchClient
          ▼                             ▼
┌────────────────────┐       ┌────────────────────────┐
│   Genie Space      │       │  Vector Search Index   │
│   GENIE_SPACE_ID   │       │  (vector_db_knowledge)  │
└─────────┬──────────┘       └──────────┬─────────────┘
          │ governed SQL                │ governed similarity search
          ▼                             ▼
┌────────────────────┐       ┌────────────────────────┐
│ reporting_flight   │       │  vector_db_knowledge   │
│ (Unity Catalog)    │       │  (Unity Catalog)       │
└────────────────────┘       └────────────────────────┘
```

Key invariants:

- The agent never sees a SQL connector or `spark.sql()` handle.
- Both data tools terminate at Unity Catalog tables, governed by the Genie service principal / Vector Search endpoint identity.
- `search_business_context` returns a JSON string with the same shape contract as `query_genie` (`text`, `sql`, `dataframe_records`, `conversation_id`) so the front-end can render both with the same code path.

## Routing table

The router lives in `SYSTEM_PROMPT`. The model must follow these rules:

| User intent | Example phrasing | Route to | Why |

## MLflow failure quick-reference

When something blows up at the MLflow / agent-server boundary, check this first. These are the failure modes we've already hit or are likely to hit during Phase 2 wiring.

| Symptom | Likely cause | Fix location |
|---|---|---|
| `mlflow.exceptions.MlflowException: Tool 'search_business_context' is not registered` at first invocation | Tool decorator missing or tool not added to the `tools` list passed into `create_agent` | `agent_server/agent.py` → `init_agent()` `tools = [...]` list |
| `databricks.vector_search.client.VectorSearchClientException: index not found` | Vector Search index name / endpoint name doesn't match what Part 1 created, or env vars not set in `app.yaml` | `agent_server/agent.py` constants (`VECTOR_SEARCH_ENDPOINT`, `VECTOR_SEARCH_INDEX_NAME`) + `app.yaml` env block |
| `403 PERMISSION_DENIED` calling Vector Search | App service principal lacks `USE ENDPOINT` on the Vector Search endpoint or `SELECT` on `vector_db_knowledge` | Databricks UI → Vector Search endpoint → Permissions, and Unity Catalog → `slf_srvc.test_db.vector_db_knowledge` → Permissions |
| Agent answers policy questions with a hallucinated definition instead of calling the tool | `SYSTEM_PROMPT` routing rules unclear or contradict the tool docstring | `agent_server/agent.py` → `SYSTEM_PROMPT` and the `search_business_context` docstring (the model reads both) |
| `TypeError: search_business_context() got an unexpected keyword argument 'config'` in MLflow trace | Tool signature wrong — `@tool` functions must accept only documented arguments; LangChain injects `config` only if you opt in | `agent_server/agent.py` → tool function signature (keep it `(question: str) -> str`) |
| MLflow trace shows the tool was called but the response is `"[]"` or `""` | Vector Search index has zero rows, or the embedding column / primary key columns in the index config don't match the table schema from Part 0 | Re-run Part 0 audit + Part 1 index creation; verify `index.describe()` shows `indexed_row_count > 0` |
| `mlflow.genai.agent_server` import fails on app startup | MLflow version in `requirements.txt` doesn't expose `agent_server` (needs MLflow ≥ 3.x with `mlflow[genai]`) | `agent-langgraph/requirements.txt` |
| Streamlit / front-end shows raw JSON instead of formatted answer | Front-end expected `text` / `dataframe_records` / `sql` keys (the `query_genie` shape); `search_business_context` returned a different shape | `agent_server/agent.py` → `search_business_context` return — keep the same JSON contract: `{"text": ..., "sql": "", "dataframe_records": [...], "conversation_id": ""}` |

## Workflow

1. Drop all 4 part files alongside this index in `agent-langgraph/`.
2. In the Cline Kanban Agent, point it at one file at a time, in order:
   - `Implement 202605151218PM_implementation_part0.md. Read the file, follow its instructions, create one Kanban task for it, and start it.`
   - Wait for it to finish. Part 0 has no code changes — it produces an audit note.
   - Repeat for `part1` (Vector Search index creation, Databricks-side, no app code change), then `part2` (adds the tool — auto-commit), then `part3` (prompt + cleanup — auto-commit).
3. After Part 3 commits, run the **manual smoke test**:
   - Start the app locally (whatever the team's standard local-run command is for `agent-langgraph/`).
   - Send three test prompts and verify routing in the MLflow trace UI:
     1. `"how many flights did we operate last week?"` → expect a `query_genie` tool call.
     2. `"what does deadhead mean in our glossary?"` → expect a `search_business_context` tool call with non-empty results.
     3. `"what time is it?"` → expect a `get_current_time` tool call.
   - Open MLflow Experiments → latest run → Traces tab. Each test should show exactly one tool call with the expected name. If routing is wrong, jump to the **MLflow failure quick-reference** table above.

## Why this works

Same reason as Phase 1: one file per task keeps each Cline turn small enough to dodge the body-timeout. Part 0 and Part 1 don't touch code, so they're cheap. Part 2 and Part 3 are the only turns that produce a commit, and each is a single, contained edit to `agent_server/agent.py`.

## If a part still times out

Same playbook as Phase 1:

```bash
# Check current timeout
grep -i timeout ~/litellm_config.yaml

# If missing or low (< 300), add or raise it:
#   request_timeout: 600
```

Restart the LiteLLM proxy and retry the failing part.

|---|---|---|---|
| Flight data, aggregates, row-level lookups | "how many flights last week", "show me top 10 routes by delay", "average leg duration in October" | `query_genie` | Structured questions answerable from `reporting_flight` via SQL |
| Policy, glossary, definition, documentation | "what does *deadhead* mean", "what is the cancellation policy", "define on-time performance" | `search_business_context` | Unstructured reference content lives in `vector_db_knowledge`; semantic search fits |
| Time / date | "what time is it", "what's today's date" | `get_current_time` | Pure clock call, no data access |
| Unrelated / out of scope | "write me a poem", "what's the weather", "stock price of AAPL" | **Refuse** | Tell the user clearly the assistant only covers flight data + policies. Do **not** guess, do **not** call a tool. |

Edge cases the prompt should explicitly cover:

- **Mixed questions** ("what's our cancellation policy and how many cancellations did we have last week?") → call `search_business_context` *and* `query_genie`, then combine in the final answer.
- **Ambiguous "policy" questions that smell like data** ("how many policy violations") → prefer `query_genie` if the answer is a count / aggregate.
