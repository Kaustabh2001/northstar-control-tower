import {
  Alert,
  Button,
  Chip,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import type { AssetDetail } from "../../../types";
import {
  type AssetDetailTab,
  AssetTimeline,
  MetadataValue,
} from "../shared";

export function McpServerDetail({
  detail,
  tab,
  onRefresh,
  refreshing,
}: {
  detail: AssetDetail;
  tab: AssetDetailTab;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const metadata = detail.metadata;
  const tools =
    detail.live_status?.tools ??
    metadata.declared_tools?.map((name: string) => ({ name }));
  if (tab === "structure") {
    return (
      <Paper className="content-card">
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <div>
            <Typography className="section-heading" variant="h6">Discovered tools & schemas</Typography>
            <Typography variant="body2" color="text.secondary">Schemas come from a live MCP initialize/list-tools exchange.</Typography>
          </div>
          <Button variant="outlined" onClick={onRefresh} disabled={refreshing}>Refresh live</Button>
        </Stack>
        <div className="tool-grid">
          {(tools ?? []).map((tool: any) => (
            <div className="skill-card" key={tool.name}>
              <strong>{tool.name}</strong>
              <p>{tool.description ?? "Declared in the governed server record; refresh to retrieve its live schema."}</p>
              {tool.inputSchema && <pre className="schema-code">{JSON.stringify(tool.inputSchema, null, 2)}</pre>}
            </div>
          ))}
        </div>
      </Paper>
    );
  }
  if (tab === "governance") {
    return (
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Access policy</Typography>
          <div className="metadata-grid top-gap">
            <MetadataValue label="Authentication" value={metadata.auth?.method} />
            <MetadataValue label="Default action" value={metadata.policy?.default_action} />
            <MetadataValue label="Network zone" value={metadata.policy?.network_zone} />
            <MetadataValue label="Secret storage" value={metadata.auth?.secret_storage} />
          </div>
          <Typography className="subsection-heading">Required roles</Typography>
          <Stack direction="row" gap={1}>{metadata.auth?.required_roles?.map((role: string) => <Chip key={role} label={role} size="small" />)}</Stack>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Human approval boundary</Typography>
          <Typography className="body-emphasis">High-impact tools remain denied unless the caller carries an authorised identity and the workflow supplies review evidence.</Typography>
          {(metadata.policy?.human_approval_for ?? []).map((item: string) => <Chip key={item} label={item.replaceAll("_", " ")} color="warning" size="small" sx={{ mr: 1 }} />)}
        </Paper>
      </div>
    );
  }
  if (tab === "activity") return <AssetTimeline detail={detail} />;
  const live = detail.live_status;
  return (
    <div className="detail-grid">
      <Paper className="content-card">
        <Stack direction="row" justifyContent="space-between">
          <Typography className="section-heading" variant="h6">Protocol endpoint</Typography>
          <Chip size="small" color={live?.reachable ? "success" : live ? "error" : "default"} label={live?.reachable ? "Live" : live ? "Unavailable" : "Not checked"} />
        </Stack>
        <Typography className="body-emphasis">{metadata.endpoint}</Typography>
        <div className="metadata-grid">
          <MetadataValue label="Transport" value={metadata.transport} />
          <MetadataValue label="Exposure" value={metadata.exposure} />
          <MetadataValue label="Declared protocol" value={metadata.protocol_version} />
          <MetadataValue label="Negotiated protocol" value={live?.protocol_version} />
          <MetadataValue label="Server" value={live?.server?.name} />
        </div>
        {live?.error && <Alert severity="warning" sx={{ mt: 2 }}>{live.error}</Alert>}
        <Button sx={{ mt: 2 }} variant="contained" onClick={onRefresh} disabled={refreshing}>{refreshing ? "Discovering…" : "Run live discovery"}</Button>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Connections</Typography>
        <Typography className="subsection-heading">Dependencies</Typography>
        <Stack spacing={1}>{metadata.dependencies?.map((item: string) => <Chip key={item} variant="outlined" label={item} />)}</Stack>
        <Typography className="subsection-heading">Tool exposure</Typography>
        <Typography variant="body2" color="text.secondary">{tools?.length ?? 0} governed tools declared or discovered.</Typography>
      </Paper>
    </div>
  );
}
