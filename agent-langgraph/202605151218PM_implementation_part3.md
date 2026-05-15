# Implementation — Phase 2 Part 3: Update SYSTEM_PROMPT, Tool Routing, and Cleanup

> **Scope:** Edit ONLY `agent_server/agent.py`.
> **Auto-review:** enabled, commit mode.
> **Prerequisites:** Phase 2 Part 1 (`answer_flight_question` tool added) and Phase 2 Part 2 (vector-search retriever wired to the new tool) must be committed.

## Goal

Update `SYSTEM_PROMPT` so the model explicitly routes questions to one of three tools — `query_genie`, `answer_flight_question`, and `get_current_time` — and (optionally) drop the now-redundant `VECTOR_SEARCH_MCP_URL` MCP wiring inside `init_agent` if `answer_flight_question` fully replaces it.

The current `SYSTEM_PROMPT` references "the vector search tool" (the MCP-injected tool from Phase 1). After Phase 2, the vector-search retrieval is exposed to the agent as a first-class `@tool` named `answer_flight_question`, so the prompt must name it directly.

## Changes inside `agent_server/agent.py`

### 1. Replace `SYSTEM_PROMPT` with the three-tool routing version

Replace the existing `SYSTEM_PROMPT` constant (lines ~159–174) with the text below. Keep it as a single triple-quoted-or-concatenated string assigned to the `SYSTEM_PROMPT` name — do not rename the constant.

```python
SYSTEM_PROMPT = (
    "You are a business intelligence assistant for the flight operations team. "
    "You have exactly three tools available, and you MUST route every question "
    "to the correct one:\n"
    "\n"
    "1. `query_genie` — use this for any question about flight DATA: row counts, "
    "aggregates, trends, specific records, 'show me…', 'how many…', "
    "'what is the average…', 'list the flights where…', or anything that can be "
    "answered by querying the table slf_srvc.test_db.reporting_flight. "
    "Always call this tool for data/SQL questions and base your answer on its "
    "response.\n"
    "\n"
    "2. `answer_flight_question` — use this for any question about POLICIES, "
    "GLOSSARY terms, DEFINITIONS, documentation, or knowledge-base content: "
    "'what does X mean', 'what is the policy for…', 'explain the term…', "
    "'how is <field> defined', or any lookup that requires unstructured "
    "reference material rather than tabular data.\n"
    "\n"
    "3. `get_current_time` — use this only when the user asks for the current "
    "date or time, or when you need 'now' to answer a relative-time question.\n"
    "\n"
    "Rules you MUST follow:\n"
    "- Never invent or fabricate data. If none of the three tools fits the "
    "question, tell the user clearly that you cannot help with that request.\n"
    "- Never execute SQL directly. All data access goes through `query_genie`. "
    "Do not use `databricks-sql-connector`, `spark.sql()`, or any other direct "
    "database interface.\n"
    "- Never answer policy/glossary/definition questions from your own training "
    "knowledge — always go through `answer_flight_question` so the answer is "
    "grounded in the approved knowledge base.\n"
    "- If a question mixes data and policy (e.g. 'how many on-time flights last "
    "month, and what is the on-time policy?'), call both tools and combine the "
    "results in your final answer."
)
```

### 2. (Optional cleanup) Remove the MCP wiring if `answer_flight_question` fully replaces it

If Phase 2 Part 2 confirms `answer_flight_question` is the only knowledge-base path, simplify `init_agent` to a static tool list and drop the `VECTOR_SEARCH_MCP_URL` branch:

```python
async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time, query_genie, answer_flight_question]
    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
    return create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
```

If you keep the MCP block as a fallback, leave `init_mcp_client` and the `VECTOR_SEARCH_MCP_URL` env constant in place but ensure `answer_flight_question` is unconditionally added to `tools` first:

```python
async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time, query_genie, answer_flight_question]
    if VECTOR_SEARCH_MCP_URL:
        try:
            mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
            tools.extend(await mcp_client.get_tools())
        except Exception:
            logger.warning(
                "Vector Search MCP unavailable; continuing without it.",
                exc_info=True,
            )
    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
    return create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
```

Pick one of the two variants. The default recommendation is the first (full removal), since the prompt now names exactly three tools and an extra MCP tool would confuse routing.

If you choose the full-removal variant, also delete:
- the `VECTOR_SEARCH_MCP_URL` constant (line ~35)
- the `init_mcp_client` function (lines ~147–156)
- the `DatabricksMCPServer, DatabricksMultiServerMCPClient` names from the `databricks_langchain` import on line ~9 (keep `ChatDatabricks`)

### 3. Sanity check imports

After cleanup, confirm `agent.py` still imports:
- `ChatDatabricks` from `databricks_langchain`
- `create_agent` from `langchain.agents`
- `tool` from `langchain_core.tools`

## What NOT to do in this task

- Do NOT touch any file other than `agent_server/agent.py`.
- Do NOT change the implementation of `query_genie`, `get_current_time`, or `answer_flight_question`. Phase 2 Parts 1 and 2 own those.
- Do NOT change the LLM endpoint or the streaming/invoke handlers.
- Do NOT edit `streamlit-hello-world-app/` or any sibling project.
- Do NOT add a fourth tool.

## Acceptance criteria

- `SYSTEM_PROMPT` is the new three-tool routing text shown above, naming `query_genie`, `answer_flight_question`, and `get_current_time` explicitly.
- `init_agent`'s `tools` list contains exactly those three tools (or those three plus an optional MCP fallback if you chose the keep-as-fallback variant).
- If you removed MCP, `VECTOR_SEARCH_MCP_URL`, `init_mcp_client`, and the unused `databricks_langchain` MCP imports are gone, and `python -c "import agent_server.agent"` runs without `NameError` / `ImportError`.
- File parses without syntax errors (`python -m py_compile agent_server/agent.py`).
- One commit with the message:
  `T6: route SYSTEM_PROMPT to query_genie / answer_flight_question / get_current_time and drop MCP wiring`
  (Use `…and keep MCP fallback` instead of `…and drop MCP wiring` if you chose the fallback variant.)

## After this part — manual smoke test

Phase 2 is complete after this commit. Run a quick 4-question smoke test against the agent endpoint (or via the Streamlit reference app pointed at this backend) to confirm routing:

1. **Data question** — "How many flights departed last month?"
   → Expected: model calls `query_genie`, returns a count grounded in `slf_srvc.test_db.reporting_flight`.

2. **Knowledge-base question** — "What does 'on-time arrival' mean in our policy?"
   → Expected: model calls `answer_flight_question`, returns the definition from the vector-search index, **not** from training knowledge.

3. **Time question** — "What is the current date?"
   → Expected: model calls `get_current_time` and returns the ISO timestamp.

4. **Out-of-scope question** — "What's the weather in Toronto right now?"
   → Expected: model calls no tool (or refuses cleanly) and tells the user it cannot help with that request, per the "Never invent or fabricate data" rule.

If any of the four routes to the wrong tool, re-open `SYSTEM_PROMPT` and tighten the wording for that category before opening the next phase.
