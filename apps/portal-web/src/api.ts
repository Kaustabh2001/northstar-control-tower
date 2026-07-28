import { getAccessToken } from "./auth";
import type {
  AgentDetail,
  Asset,
  AssetDetail,
  AssetType,
  DashboardSummary,
  GovernanceState,
  GovernanceApproval,
  GovernancePortfolio,
  McpInvocation,
  NewAsset,
  RunDetail,
  RuntimePortfolio,
  DummyRunRequest,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
    ...init,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getDashboard(): Promise<DashboardSummary> {
  return request("/api/v1/dashboard");
}

export function getAssets(type: AssetType | "all", query: string): Promise<Asset[]> {
  const params = new URLSearchParams();
  if (type !== "all") params.set("asset_type", type);
  if (query.trim()) params.set("query", query.trim());
  const suffix = params.size ? `?${params}` : "";
  return request(`/api/v1/assets${suffix}`);
}

export function registerAsset(asset: NewAsset): Promise<Asset> {
  return request("/api/v1/assets", {
    method: "POST",
    body: JSON.stringify(asset),
  });
}

export function getAgentDetail(
  assetId: string,
  version: string,
): Promise<AgentDetail> {
  return request(`/api/v1/agents/${encodeURIComponent(assetId)}/versions/${encodeURIComponent(version)}`);
}

export function getAssetDetail(
  assetId: string,
  version: string,
  refreshLive = false,
): Promise<AssetDetail> {
  const live = refreshLive ? "?refresh_live=true" : "";
  return request(
    `/api/v1/assets/${encodeURIComponent(assetId)}/versions/${encodeURIComponent(version)}/detail${live}`,
  );
}

export function transitionAgent(
  assetId: string,
  version: string,
  targetState: GovernanceState,
  note: string,
): Promise<AgentDetail> {
  return request(
    `/api/v1/agents/${encodeURIComponent(assetId)}/versions/${encodeURIComponent(version)}/governance-state`,
    {
      method: "POST",
      body: JSON.stringify({ target_state: targetState, note }),
    },
  );
}

export function getGovernancePortfolio(): Promise<GovernancePortfolio> {
  return request("/api/v1/governance");
}

export function decideApproval(
  approvalId: string,
  decision: "approve" | "reject",
  note: string,
): Promise<GovernanceApproval> {
  return request(`/api/v1/governance/approvals/${approvalId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, note }),
  });
}

export function getRuntimePortfolio(): Promise<RuntimePortfolio> {
  return request("/api/v1/runtime");
}

export function requestApproval(
  assetId: string,
  version: string,
  targetState: GovernanceState,
  note: string,
): Promise<GovernanceApproval> {
  return request(
    `/api/v1/assets/${encodeURIComponent(assetId)}/versions/${encodeURIComponent(version)}/approvals`,
    {
      method: "POST",
      body: JSON.stringify({ target_state: targetState, note }),
    },
  );
}

export function startDummyRun(input: DummyRunRequest): Promise<RunDetail> {
  return request("/api/v1/runtime/dummy-runs", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function performEmergencyAction(
  assetId: string,
  version: string,
  action: "suspend" | "rollback",
  reason: string,
  targetVersion?: string,
): Promise<Asset> {
  return request(
    `/api/v1/assets/${encodeURIComponent(assetId)}/versions/${encodeURIComponent(version)}/emergency-action`,
    {
      method: "POST",
      body: JSON.stringify({
        action,
        reason,
        target_version: targetVersion ?? null,
      }),
    },
  );
}

export function getRunDetail(runId: string): Promise<RunDetail> {
  return request(`/api/v1/runtime/runs/${runId}`);
}

export function decideHumanReview(
  reviewId: string,
  decision: "approve" | "reject" | "request_changes",
  rationale: string,
): Promise<RunDetail> {
  return request(`/api/v1/runtime/reviews/${reviewId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, rationale }),
  });
}

export function getMcpInvocations(): Promise<McpInvocation[]> {
  return request("/api/v1/mcp-gateway/invocations");
}
