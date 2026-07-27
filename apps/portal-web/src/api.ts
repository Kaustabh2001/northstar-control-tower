import type { Asset, AssetType, DashboardSummary, NewAsset } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
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
