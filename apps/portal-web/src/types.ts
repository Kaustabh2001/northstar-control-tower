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

export interface GovernanceApproval {
  approval_id: string;
  asset_id: string;
  version: string;
  display_name: string;
  asset_type: AssetType;
  current_state: GovernanceState;
  target_state: GovernanceState;
  status: "pending" | "approved" | "rejected";
  requested_by: string;
  request_note: string;
  decided_by: string | null;
  decision_note: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface GovernanceEvidence {
  evidence_id: string;
  asset_id: string;
  version: string;
  evidence_type: string;
  title: string;
  status: string;
  reference: string;
  collected_by: string;
  created_at: string;
}

export interface GovernancePortfolio {
  approvals: GovernanceApproval[];
  evidence: GovernanceEvidence[];
  state_counts: Record<string, number>;
  allowed_transitions: Record<string, GovernanceState[]>;
}

export interface RuntimeStage {
  stage_id: string;
  display_name: string;
  status: string;
  kind: string;
  started_at: string | null;
  completed_at: string | null;
  attempt: number;
  summary: string | null;
}

export interface WorkflowRun {
  run_id: string;
  workflow_asset_id: string;
  workflow_version: string;
  workflow_name: string;
  status: string;
  current_stage_id: string | null;
  correlation: Record<string, any>;
  stages: RuntimeStage[];
  checkpoint_ref: string | null;
  error_code: string | null;
  error_summary: string | null;
  started_at: string;
  updated_at: string;
}

export interface HumanReview {
  review_id: string;
  run_id: string;
  stage_id: string;
  title: string;
  reason: string;
  policy_evidence: string[];
  requested_action: Record<string, any>;
  status: string;
  requested_at: string;
  expires_at: string;
  decided_by: string | null;
  decision: string | null;
  rationale: string | null;
  decided_at: string | null;
}

export interface RuntimePortfolio {
  runs: WorkflowRun[];
  reviews: HumanReview[];
  status_counts: Record<string, number>;
}

export interface RuntimeEvent {
  event_id: string;
  run_id: string;
  event_type: string;
  stage_id: string | null;
  actor_id: string;
  payload: Record<string, any>;
  occurred_at: string;
}

export interface RunDetail {
  run: WorkflowRun;
  events: RuntimeEvent[];
  review: HumanReview | null;
}

export interface DummyRunRequest {
  request_id: string;
  requester: string;
  application: string;
  entitlement: string;
}

export interface McpInvocation {
  request_id: string;
  server_asset_id: string;
  tool_name: string;
  run_id: string | null;
  stage_id: string | null;
  actor_email: string;
  decision: string;
  reason: string;
  arguments: Record<string, any>;
  result: Record<string, any> | null;
  created_at: string;
}
