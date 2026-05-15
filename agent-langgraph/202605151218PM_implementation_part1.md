# Implementation — Phase 2 / Part 1: Create Vector Search Index on `business_context`

> **Scope:** Databricks UI or CLI/SDK only. **NO code changes** to `agent-langgraph/`.
> No edits to `agent_server/agent.py`, `agent_server/app.py`, `requirements.txt`, or any other file in this repo.
> **Streamlit reference** (`streamlit-hello-world-app/`) is read-only — do not modify.
> **Auto-review:** enabled, commit mode (this task produces only this `.md` file as a deliverable).

## Skip condition

If **Phase 2 Part 0** (preflight) confirmed that the index `slf_srvc.test_db.vector_db_knowledge_index` already exists **and** its status is `ONLINE` (or `READY`), **skip this task entirely** and proceed to `implementation_part2.md`. Do not recreate the index.

Quick re-check before skipping:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
idx = w.vector_search_indexes.get_index("slf_srvc.test_db.vector_db_knowledge_index")
print(idx.status.detailed_state, idx.status.ready)
```

If `ready is True` and `detailed_state` is `ONLINE` / `ONLINE_NO_PENDING_UPDATE`, skip.

## Goal

Create a **Delta Sync Vector Search index** named `slf_srvc.test_db.vector_db_knowledge_index` over the source table `slf_srvc.test_db.business_context`, with `id` as the primary key. The index must be `ONLINE` and return results for a sample query before we wire it into the agent in later parts.

This index is the data backing for the `vector_search` MCP tool the LangGraph agent will call alongside `query_genie`.

## Source table assumptions

- Table: `slf_srvc.test_db.business_context`
- Primary key column: `id` (non-null, unique)
- Text column to embed: `content` (rename below if your table uses a different column)
- Change Data Feed (CDF) is enabled on the table (required for Delta Sync indexes). To verify:
  ```sql
  DESCRIBE TABLE EXTENDED slf_srvc.test_db.business_context;
  -- Look for: delta.enableChangeDataFeed = true
  ```
  If not enabled:
  ```sql
  ALTER TABLE slf_srvc.test_db.business_context
  SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
  ```

## Option A — Databricks UI (recommended for one-off creation)

1. Open **Databricks workspace** → left nav → **Catalog**.
2. Navigate to `slf_srvc` → `test_db` → `business_context`.
3. Click the **Create** button (top-right of the table page) → **Vector search index**.
   - (Equivalent path on some workspaces: open the table, switch to the **Indexes** tab → **Create vector search index**.)
4. Fill in the dialog:
   - **Name:** `vector_db_knowledge_index`
   - **Catalog / Schema:** `slf_srvc` / `test_db` (so the full name becomes `slf_srvc.test_db.vector_db_knowledge_index`)
   - **Primary key:** `id`
   - **Endpoint:** select your existing Vector Search endpoint (e.g. `vs-endpoint-shared`). If none exists, create one first under **Compute → Vector Search**.
   - **Index type:** **Delta Sync index** (keeps the index continuously synced with the Delta table via CDF).
   - **Sync mode:** **Continuous** (preferred) or **Triggered** if you want manual control.
   - **Embedding source:**
     - **Compute embeddings (recommended for first pass):**
       - **Source column:** `content`
       - **Embedding model endpoint:** `databricks-gte-large-en` (or `databricks-bge-large-en`)
     - **Use pre-computed embeddings** (only if `business_context` already has a vector column):
       - **Embedding vector column:** `embedding`
       - **Embedding dimension:** match the model that produced it (e.g. `1024` for `gte-large-en`)
5. Click **Create**. The index will go through `PROVISIONING` → `ONLINE`. Initial backfill can take a few minutes depending on row count.

## Option B — Python SDK (scriptable, repeatable)

Run this in a Databricks notebook or a local Python with `databricks-sdk` configured (auth via `DATABRICKS_HOST` + `DATABRICKS_TOKEN` or default profile).

### B.1 — Compute embeddings on the fly (default recommendation)

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    PipelineType,
    VectorIndexType,
)

w = WorkspaceClient()

INDEX_NAME    = "slf_srvc.test_db.vector_db_knowledge_index"
SOURCE_TABLE  = "slf_srvc.test_db.business_context"
ENDPOINT_NAME = "vs-endpoint-shared"   # <-- replace with your VS endpoint
PRIMARY_KEY   = "id"
SOURCE_COLUMN = "content"
EMBED_MODEL   = "databricks-gte-large-en"

w.vector_search_indexes.create_index(
    name=INDEX_NAME,
    endpoint_name=ENDPOINT_NAME,
    primary_key=PRIMARY_KEY,
    index_type=VectorIndexType.DELTA_SYNC,
    delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
        source_table=SOURCE_TABLE,
        pipeline_type=PipelineType.CONTINUOUS,    # or PipelineType.TRIGGERED
        embedding_source_columns=[
            EmbeddingSourceColumn(
                name=SOURCE_COLUMN,
                embedding_model_endpoint_name=EMBED_MODEL,
            ),
        ],
    ),
)
print(f"Create requested: {INDEX_NAME}")
```

### B.2 — Use pre-computed embeddings (only if your table already has a vector column)

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingVectorColumn,
    PipelineType,
    VectorIndexType,
)

w = WorkspaceClient()

INDEX_NAME    = "slf_srvc.test_db.vector_db_knowledge_index"
SOURCE_TABLE  = "slf_srvc.test_db.business_context"
ENDPOINT_NAME = "vs-endpoint-shared"
PRIMARY_KEY   = "id"
EMBED_COLUMN  = "embedding"   # existing ARRAY<FLOAT> column on the table
EMBED_DIM     = 1024          # must match the model that produced the vectors

w.vector_search_indexes.create_index(
    name=INDEX_NAME,
    endpoint_name=ENDPOINT_NAME,
    primary_key=PRIMARY_KEY,
    index_type=VectorIndexType.DELTA_SYNC,
    delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
        source_table=SOURCE_TABLE,
        pipeline_type=PipelineType.CONTINUOUS,
        embedding_vector_columns=[
            EmbeddingVectorColumn(
                name=EMBED_COLUMN,
                embedding_dimension=EMBED_DIM,
            ),
        ],
    ),
)
print(f"Create requested: {INDEX_NAME}")
```

> Pick **B.1 or B.2**, not both. B.1 is the default; only use B.2 if the source table already stores a precomputed embedding column.

## Verification

### V.1 — Wait for `ONLINE`

```python
import time
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
INDEX_NAME = "slf_srvc.test_db.vector_db_knowledge_index"

for _ in range(60):  # up to ~10 minutes
    idx = w.vector_search_indexes.get_index(INDEX_NAME)
    state = idx.status.detailed_state
    ready = idx.status.ready
    print(f"state={state} ready={ready}")
    if ready:
        break
    time.sleep(10)
```

Expected terminal state: `ready=True` and `detailed_state` containing `ONLINE` (e.g. `ONLINE_NO_PENDING_UPDATE`).

### V.2 — Sample query against the index

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
INDEX_NAME = "slf_srvc.test_db.vector_db_knowledge_index"

result = w.vector_search_indexes.query_index(
    index_name=INDEX_NAME,
    query_text="What does on-time performance mean for a flight?",
    columns=["id", "content"],
    num_results=3,
)

# result.result.data_array is a list of rows in the order of `columns` + score
for row in result.result.data_array or []:
    print(row)
```

(For the pre-computed-embeddings variant from B.2, replace `query_text=...` with `query_vector=[...]` of the right dimension.)

### V.3 — Spot-check via UI

In **Catalog → `slf_srvc.test_db.vector_db_knowledge_index`**, the index page should show:
- Status: **Online**
- Source table: `slf_srvc.test_db.business_context`
- Primary key: `id`
- A **Test query** panel that returns at least one row for a generic question.

## Acceptance criteria

- Index `slf_srvc.test_db.vector_db_knowledge_index` exists on the chosen Vector Search endpoint.
- `w.vector_search_indexes.get_index(...)` reports `ready=True` and `detailed_state` includes `ONLINE`.
- `query_index(query_text="...", num_results=3)` returns ≥ 1 row with `id` and `content` populated.
- **No code commits in `agent-langgraph/`** as a result of this task. The only file produced by Cline for this part is this `.md` (and its mirror under the central `Documentation/` folder).
- The Vector Search endpoint name and embedding model used are recorded (you'll need them in Part 2 when configuring the MCP tool / env vars).

## What NOT to do in this task

- Do NOT modify `agent_server/agent.py`, `agent_server/app.py`, or any other source file.
- Do NOT add or change `requirements.txt` / `pyproject.toml`.
- Do NOT wire the index into the agent yet — that's Part 2.
- Do NOT delete or recreate the index if Part 0 already confirmed it is `ONLINE` (see Skip condition above).
- Do NOT hardcode the Vector Search endpoint name in any committed file.

## Next

When the index is `ONLINE` and the sample query returns results, proceed to `implementation_part2.md` (Phase 2 Part 2): configure the Vector Search MCP tool / `VECTOR_SEARCH_MCP_URL` env wiring and add the `vector_search` tool to the LangGraph agent alongside `query_genie`.
