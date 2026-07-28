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

export interface SessionUser {
  subject: string;
  email: string;
  display_name: string;
  roles: string[];
  auth_mode: string;
}

export interface AgentSkill {
  skill_id: string;
  name: string;
  description: string;
  tags: string[];
  input_modes: string[];
  output_modes: string[];
}

export interface AgentDetail {
  asset: Asset;
  agent_card: {
    name: string;
    description: string;
    protocol_version: string;
    url: string;
    preferred_transport: string;
    capabilities: Record<string, boolean>;
    skills: AgentSkill[];
  };
  dependencies: Array<{
    asset_id: string;
    version: string;
    relationship: string;
    display_name: string;
    asset_type: string;
  }>;
  controls: Array<{
    control_id: string;
    name: string;
    status: string;
    evidence: string;
  }>;
  health: {
    status: string;
    latency_ms: number | null;
    last_checked_at: string | null;
  };
  version_history: Asset[];
  audit_events: Array<{
    event_id: string;
    action: string;
    actor_email: string;
    detail: string;
    created_at: string;
  }>;
  runtime_connected: boolean;
}

export interface AssetDetail {
  asset: Asset;
  detail_kind: string;
  metadata: Record<string, any>;
  version_history: Asset[];
  audit_events: Array<{
    event_id: string;
    action: string;
    actor_email: string;
    detail: string;
    created_at: string;
  }>;
  live_status: {
    reachable: boolean;
    endpoint: string;
    protocol_version?: string;
    server?: Record<string, any>;
    capabilities?: Record<string, any>;
    tools?: Array<Record<string, any>>;
    error?: string;
  } | null;
}
