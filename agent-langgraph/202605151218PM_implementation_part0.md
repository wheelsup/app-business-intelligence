# Implementation — Phase 2 / Part 0: Audit `vector_db_knowledge` Table + Vector Search Prerequisites

> **Scope:** Databricks UI or CLI/SDK only. **NO code changes** to `agent-langgraph/`.
> No edits to `agent_server/agent.py`, `agent_server/app.py`, `requirements.txt`, or any other file in this repo.
> **Streamlit reference** (`streamlit-hello-world-app/`) is read-only — do not modify.
> **Auto-review:** enabled, commit mode (this task produces only this `.md` file as a deliverable).

## Goal

Verify that the source table `slf_srvc.test_db.vector_db_knowledge` exists, has the required schema columns, and is ready for Vector Search index creation. This is a **preflight check** — no modifications to the table itself, only inspection and optional CDF enablement.

## Prerequisites

- You have a Databricks workspace with Unity Catalog enabled.
- You have `BROWSE` access to `slf_srvc.test_db` schema.
- A Vector Search endpoint already exists (e.g. `vs-endpoint-shared`). If not, create one under **Compute → Vector Search** before proceeding to Part 1.

## Audit checklist

### A.1 — Table exists and is accessible

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
table = w.tables.get("slf_srvc.test_db.vector_db_knowledge")
print(f"Table: {table.full_name}")
print(f"Type: {table.table_type}")  # should be EXTERNAL_TABLE or MANAGED
print(f"Rows: {table.row_count}")
```

Expected output:
- `full_name` = `slf_srvc.test_db.vector_db_knowledge`
- `table_type` = `EXTERNAL_TABLE` or `MANAGED`
- `row_count` > 0 (table has data)

### A.2 — Schema includes required columns

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
table = w.tables.get("slf_srvc.test_db.vector_db_knowledge")
print(table.columns)
```

Expected columns (at minimum):
- `id` — primary key, non-null, unique (type: `STRING` or `INT`)
- `content` — text to embed (type: `STRING`)
- Optional but useful: `category`, `table_name`, `created_at`, `updated_at`

If `id` or `content` are missing or have different names, note the actual column names — you'll need them in Part 1 when creating the Vector Search index.

### A.3 — Change Data Feed (CDF) is enabled (required for Delta Sync indexes)

```sql
DESCRIBE TABLE EXTENDED slf_srvc.test_db.vector_db_knowledge;
```

Look for the line: `delta.enableChangeDataFeed = true`

If it says `false` or is missing, enable it:

```sql
ALTER TABLE slf_srvc.test_db.vector_db_knowledge
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

### A.4 — Vector Search endpoint exists

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
endpoints = w.vector_search_endpoints.list_endpoints()
for ep in endpoints:
    print(f"Endpoint: {ep.name}, State: {ep.state}")
```

Expected: at least one endpoint with `state = 'ONLINE'` (e.g. `vs-endpoint-shared`).

If no endpoints exist, create one in the Databricks UI:
- **Compute → Vector Search → Create endpoint**
- Name: e.g. `vs-endpoint-shared`
- Region: match your workspace region
- Wait for it to reach `ONLINE` state (can take 5–10 minutes).

### A.5 — Check for existing index (optional skip condition)

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
try:
    idx = w.vector_search_indexes.get_index("slf_srvc.test_db.vector_db_knowledge_index")
    print(f"Index status: {idx.status.detailed_state}")
    print(f"Ready: {idx.status.ready}")
    if idx.status.ready:
        print("✓ Index already exists and is ONLINE. You can skip Part 1 and proceed to Part 2.")
    else:
        print("⚠ Index exists but is not ready. Wait for it to reach ONLINE before proceeding.")
except Exception as e:
    print(f"Index does not exist yet (expected): {e}")
```

## Acceptance criteria

- ✓ Table `slf_srvc.test_db.vector_db_knowledge` exists and contains > 0 rows.
- ✓ Table has `id` (primary key) and `content` (text) columns.
- ✓ Change Data Feed is enabled on the table (`delta.enableChangeDataFeed = true`).
- ✓ At least one Vector Search endpoint exists and is `ONLINE`.
- ✓ If index `slf_srvc.test_db.vector_db_knowledge_index` already exists and is `ONLINE`, note that Part 1 can be skipped.
- ✓ **No code commits or file changes in `agent-langgraph/`** — this is an audit-only task.

## Next

When all checks pass, proceed to `implementation_part1.md` (Phase 2 Part 1): create the Vector Search index over `vector_db_knowledge` if it doesn't already exist.
