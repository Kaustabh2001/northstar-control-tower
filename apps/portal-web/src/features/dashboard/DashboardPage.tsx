import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Chip, Paper, Stack, Typography } from "@mui/material";

import { getDashboard } from "../../api";
import type { AssetFilter } from "../../app/navigation";
import { typeLabels } from "../../shared/assetCatalog";
import { LoadingPanel, PageHeader } from "../../shared/components";

export function DashboardPage({ onRegister }: { onRegister: () => void }) {
  const summary = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  if (summary.isPending) return <LoadingPanel />;
  if (summary.isError) {
    return <Alert severity="error">{summary.error.message}</Alert>;
  }
  const data = summary.data;
  const stats = [
    ["Managed assets", data.managed_assets, `${data.discovered_assets} discovered`, "AI"],
    ["Control coverage", "92%", "Policy evaluation enabled", "GC"],
    ["Registry reviews", data.awaiting_review, "Evidence awaiting a steward", "AP"],
    ["High-risk assets", data.high_risk_assets, "Require explicit controls", "AL"],
    ["Model provider", "Offline", "Fixture mode is active", "LLM"],
  ];
  return (
    <>
      <PageHeader
        eyebrow="Portfolio pulse"
        title="AI governance, without blind spots."
        description="Live registry data from the secured control plane."
        action={<Button variant="contained" onClick={onRegister}>Register asset</Button>}
      />
      <div className="stat-grid">
        {stats.map(([label, value, note, mark]) => (
          <Paper className="stat-card" key={label}>
            <Stack direction="row" justifyContent="space-between">
              <Typography className="metric-label" variant="caption">{label}</Typography>
              <span className="stat-mark">{mark}</span>
            </Stack>
            <strong>{value}</strong>
            <Typography variant="caption" color="text.secondary">{note}</Typography>
          </Paper>
        ))}
      </div>
      <div className="overview-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Asset composition</Typography>
          <Typography variant="body2" color="text.secondary">
            Persisted versions grouped by governed type.
          </Typography>
          <div className="composition">
            {Object.entries(data.by_type).map(([type, count]) => (
              <div className="composition-row" key={type}>
                <strong>{typeLabels[type as AssetFilter] ?? type}</strong>
                <div><i style={{ width: `${Math.max(12, count * 16)}%` }} /></div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </Paper>
        <Paper className="content-card decision-card">
          <Chip size="small" color="warning" label={`${data.awaiting_review} waiting`} />
          <Typography className="section-heading" variant="h6">Registry decisions</Typography>
          <Typography variant="body2" color="text.secondary">
            Versions cannot advance until an authorised steward verifies their evidence.
          </Typography>
          <Button variant="outlined" size="small">Open review queue</Button>
        </Paper>
      </div>
    </>
  );
}
