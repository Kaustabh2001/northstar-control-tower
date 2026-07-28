import type { AssetFilter } from "../app/navigation";

export const assetTypes: Array<{
  value: AssetFilter;
  label: string;
  mark: string;
}> = [
  { value: "all", label: "All assets", mark: "AI" },
  { value: "ai_system", label: "AI systems", mark: "SY" },
  { value: "agentic_workflow", label: "Agentic workflows", mark: "WF" },
  { value: "agent", label: "Agents", mark: "AG" },
  { value: "model", label: "Models", mark: "ML" },
  { value: "prompt", label: "Prompts", mark: "PR" },
  { value: "dataset", label: "Datasets", mark: "DS" },
  { value: "knowledge_index", label: "Knowledge indexes", mark: "KB" },
  { value: "mcp_server", label: "MCP servers", mark: "MC" },
];

export const typeLabels: Record<AssetFilter, string> = {
  all: "Asset",
  ai_system: "AI system",
  agentic_workflow: "Agentic workflow",
  agent: "Agent",
  model: "Model",
  prompt: "Prompt",
  dataset: "Dataset",
  knowledge_index: "Knowledge index",
  mcp_server: "MCP server",
};
