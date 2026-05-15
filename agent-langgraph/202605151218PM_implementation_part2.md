# Implementation — Phase 2 / Part 2: Add `search_business_context` Tool to `agent.py`

> **Scope:** Edit ONLY `agent_server/agent.py`.
> **Auto-review:** enabled, commit mode.
> **Prerequisites:** Phase 2 Part 1 (Vector Search index `slf_srvc.test_db.vector_db_knowledge_index` is `ONLINE`) must be complete.

## Goal

Add a new `@tool` named `search_business_context` to `agent_server/agent.py`. This tool will:
- Call the Vector Search index `slf_srvc.test_db.vector_db_knowledge_index` via the Databricks SDK.
- Return matched rows with `id`, `content`, `category`, and `table_name` columns.
- Return results in the same JSON shape as `query_genie` so the front-end can render both with identical code paths.
- Replace the optional MCP-based vector search with a hard-coded, always-available RAG tool.

## Changes to `agent_server/agent.py`

### 1. Add the env var constant near the top (after `LLM_ENDPOINT_NAME`, around line 35)

```python
VECTOR_SEARCH_INDEX_NAME = os.getenv("VECTOR_SEARCH_INDEX_NAME", "")  # e.g. "slf_srvc.test_db.vector_db_knowledge_index"
```

### 2. Add the `search_business_context` tool after `query_genie` (around line 120–145)

```python
@tool
def search_business_context(query: str) -> str:
    """Search the business context knowledge base for column definitions,
    business rules, glossary terms, and domain knowledge relevant to the query.
    Always call this BEFORE query_genie for any flight data question so that
    Genie receives enriched context and generates more accurate SQL.
    Returns matched context text with traceability IDs."""
    if not VECTOR_SEARCH_INDEX_NAME:
        return json.dumps({
            "text": "",
            "sql": "",
            "dataframe_records": [],
            "conversation_id": "",
        })

    try:
        vs_index = sp_workspace_client.vector_search_indexes.get_index(VECTOR_SEARCH_INDEX_NAME)
        results = vs_index.similarity_search(
            query_text=query,
            columns=["id", "content", "category", "table_name"],
            num_results=3,
        )
        rows = results.get("result", {}).get("data_array", [])
        context_pieces = [str(row[1]) for row in rows]  # column 1 = content
        
        logger.info("search_business_context retrieved %d rows for query: %s", len(rows), query)
        
        return json.dumps({
            "text": "\n".join(context_pieces),
            "sql": "",
            "dataframe_records": [{"id": str(row[0]), "content": str(row[1]), "category": str(row[2]) if len(row) > 2 else "", "table_name": str(row[3]) if len(row) > 3 else ""} for row in rows],
            "conversation_id": "",
        })
    except Exception as e:
        logger.error("search_business_context failed: %s", e, exc_info=True)
        return json.dumps({
            "text": "",
            "sql": "",
            "dataframe_records": [],
            "conversation_id": "",
        })
```

### 3. Update `init_agent` to include `search_business_context` in the tools list

Find the `init_agent` function (around line 160–175) and update the `tools` list to include `search_business_context`:

**Before:**
```python
async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time, query_genie]
    # ... rest of function
```

**After:**
```python
async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time, query_genie, search_business_context]
    # ... rest of function
```

If there is MCP wiring in `init_agent`, you can keep it as an optional fallback (it will be cleaned up in Part 3), or remove it now. The important thing is that `search_business_context` is unconditionally added to `tools`.

## Acceptance criteria

- ✓ `VECTOR_SEARCH_INDEX_NAME` constant is defined and reads from the env var (defaults to empty string).
- ✓ `search_business_context` function is defined as a `@tool` with the correct signature: `(query: str) -> str`.
- ✓ The tool returns JSON with keys: `text`, `sql`, `dataframe_records`, `conversation_id` (same shape as `query_genie`).
- ✓ The tool gracefully returns empty results if `VECTOR_SEARCH_INDEX_NAME` is not set.
- ✓ The tool gracefully catches and logs exceptions without raising to the caller.
- ✓ `init_agent` includes `search_business_context` in the `tools` list.
- ✓ File parses without syntax errors: `python -m py_compile agent_server/agent.py`.
- ✓ One commit with the message:
  ```
  T5: add search_business_context @tool backed by vector_db_knowledge_index
  ```

## Testing (manual, after commit)

1. Set `.env` (or `app.yaml` for deployed app):
   ```bash
   VECTOR_SEARCH_INDEX_NAME=slf_srvc.test_db.vector_db_knowledge_index
   ```

2. Start the backend:
   ```bash
   cd agent-langgraph && python -m agent_server.app
   ```

3. Send a test prompt to the agent:
   ```
   "What does on-time performance mean?"
   ```

4. Check MLflow Traces UI:
   - The agent should call `search_business_context` first.
   - The tool should return non-empty `text` and `dataframe_records` (if the vector index has matching rows).
   - The agent should then synthesize an answer from the retrieved context.

## Next

When the tool is working and the commit is pushed, proceed to `implementation_part3.md` (Phase 2 Part 3): update the `SYSTEM_PROMPT` to explicitly route questions to `search_business_context` and clean up any dead MCP wiring.
