import type { AssetType } from "../types";

export type Page =
  | "overview"
  | "inventory"
  | "agent"
  | "asset"
  | "lifecycle"
  | "runtime"
  | "security";

export type AssetFilter = AssetType | "all";

export interface RouteState {
  page: Page;
  assetId?: string;
  version?: string;
}

export function routeFromLocation(): RouteState {
  const typedMatch = window.location.pathname.match(
    /^\/assets\/([^/]+)\/([^/]+)\/versions\/([^/]+)$/,
  );
  if (typedMatch) {
    return {
      page: typedMatch[1] === "agent" ? "agent" : "asset",
      assetId: decodeURIComponent(typedMatch[2]),
      version: decodeURIComponent(typedMatch[3]),
    };
  }
  const legacyAgentMatch = window.location.pathname.match(
    /^\/assets\/([^/]+)\/versions\/([^/]+)$/,
  );
  if (legacyAgentMatch) {
    return {
      page: "agent",
      assetId: decodeURIComponent(legacyAgentMatch[1]),
      version: decodeURIComponent(legacyAgentMatch[2]),
    };
  }
  const topLevel = window.location.pathname.slice(1) as Page;
  if (["inventory", "lifecycle", "runtime", "security"].includes(topLevel)) {
    return { page: topLevel };
  }
  return { page: "overview" };
}
