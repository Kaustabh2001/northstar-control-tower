export type AssetType =
  | "ai_system"
  | "agentic_workflow"
  | "agent"
  | "model"
  | "prompt"
  | "dataset"
  | "knowledge_index"
  | "mcp_server";

export type GovernanceState =
  | "discovered"
  | "registered"
  | "assess"
  | "build_test"
  | "steward_review"
  | "shadow"
  | "canary"
  | "production"
  | "suspended"
  | "retired";

export interface Asset {
  asset_id: string;
  version: string;
  asset_type: AssetType;
  display_name: string;
  owner: string;
  intended_use: string;
  prohibited_uses: string[];
  governance_state: GovernanceState;
  risk_level: "unassessed" | "low" | "medium" | "high" | "unacceptable";
  source_commit: string | null;
  labels: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  total_assets: number;
  managed_assets: number;
  discovered_assets: number;
  awaiting_review: number;
  high_risk_assets: number;
  by_type: Record<string, number>;
  model_provider: string;
}

export type NewAsset = Pick<
  Asset,
  "asset_id" | "version" | "asset_type" | "display_name" | "owner" | "intended_use"
>;
