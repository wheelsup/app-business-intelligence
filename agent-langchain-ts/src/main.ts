import { config } from "dotenv";
import { existsSync } from "fs";

// Load .env.local first (if present) for local-only overrides, then .env.
// Variables set in .env.local take precedence (dotenv won't override existing values).
if (existsSync(".env.local")) {
  config({ path: ".env.local" });
  console.log("📄 Loaded .env.local");
}
config();

import { createAgent } from "./agent.js";
import { getMCPServers } from "./mcp-servers.js";
import { startServer } from "./framework/server.js";

// When using LiteLLM locally, skip Databricks-specific MCP servers
const useLiteLLM = !!process.env.LITELLM_BASE_URL;
const mcpServers = useLiteLLM ? [] : getMCPServers();

const agent = await createAgent({
  model: process.env.DATABRICKS_MODEL || "databricks-claude-sonnet-4-5",
  temperature: parseFloat(process.env.TEMPERATURE || "0.1"),
  maxTokens: parseInt(process.env.MAX_TOKENS || "2000", 10),
  useResponsesApi: process.env.USE_RESPONSES_API === "true",
  mcpServers,
});

startServer(agent).catch((error) => {
  console.error("❌ Failed to start server:", error);
  process.exit(1);
});
