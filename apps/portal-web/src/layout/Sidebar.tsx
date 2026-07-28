import { Box, Stack } from "@mui/material";

import type { AssetFilter, Page } from "../app/navigation";
import { assetTypes } from "../shared/assetCatalog";

export function Sidebar({
  page,
  assetFilter,
  onNavigate,
  onAssetFilter,
}: {
  page: Page;
  assetFilter: AssetFilter;
  onNavigate: (page: Page) => void;
  onAssetFilter: (type: AssetFilter) => void;
}) {
  const navigation: Array<[Page, string, string]> = [
    ["overview", "OV", "Overview"],
    ["inventory", "AI", "Asset inventory"],
    ["lifecycle", "LC", "Governance lifecycle"],
    ["runtime", "RT", "Runtime operations"],
    ["security", "SC", "Security & privacy"],
  ];
  const inventoryActive = ["inventory", "agent", "asset"].includes(page);
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">NS</span>
        <div><strong>Northstar</strong><small>Local AI Control Tower</small></div>
      </div>
      <span className="nav-label">Control plane</span>
      <nav>
        {navigation.map(([value, mark, label]) => (
          <Box key={value}>
            <button
              className={page === value || (value === "inventory" && inventoryActive) ? "nav-button active" : "nav-button"}
              onClick={() => onNavigate(value)}
            >
              <span className="nav-mark">{mark}</span><strong>{label}</strong>
            </button>
            {value === "inventory" && (
              <div className="asset-subnav">
                {assetTypes.map((type) => (
                  <button
                    key={type.value}
                    className={inventoryActive && assetFilter === type.value ? "active" : ""}
                    onClick={() => onAssetFilter(type.value)}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            )}
          </Box>
        ))}
      </nav>
      <div className="provider-status">
        <Stack direction="row" justifyContent="space-between">
          <strong>Model provider</strong><span className="amber-dot" />
        </Stack>
        <p>Not configured. Registry and governance remain available.</p>
      </div>
    </aside>
  );
}
