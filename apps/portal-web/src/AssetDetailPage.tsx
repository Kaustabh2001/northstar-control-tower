import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from "@mui/material";

import { getAssetDetail } from "./api";
import type { Asset, AssetDetail } from "./types";

type DetailTab = "overview" | "structure" | "governance" | "activity";

function LabelValue({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="label-value">
      <span>{label}</span>
      <strong>{String(value ?? "Not recorded").replaceAll("_", " ")}</strong>
    </div>
  );
}

function StateChip({ asset }: { asset: Asset }) {
  return (
    <Chip
      size="small"
      color={asset.governance_state === "production" ? "success" : "warning"}
      label={asset.governance_state.replaceAll("_", " ")}
      sx={{ textTransform: "capitalize", fontWeight: 800 }}
    />
  );
}

function Timeline({ detail }: { detail: AssetDetail }) {
  if (!detail.audit_events.length) {
    return <Alert severity="info">No audit events have been recorded for this version.</Alert>;
  }
  return (
    <Paper className="content-card">
      <Typography className="section-heading" variant="h6">Version audit trail</Typography>
      <div className="timeline">
        {detail.audit_events.map((event) => (
          <div className="timeline-item" key={event.event_id}>
            <i />
            <div>
              <strong>{event.action.replaceAll(".", " ")}</strong>
              <p>{event.detail}</p>
              <small>{event.actor_email} · {new Date(event.created_at).toLocaleString()}</small>
            </div>
          </div>
        ))}
      </div>
    </Paper>
  );
}

function DatasetDetail({ detail, tab }: { detail: AssetDetail; tab: DetailTab }) {
  const metadata = detail.metadata;
  const source = metadata.source ?? {};
  const quality = metadata.quality ?? {};
  const lineage = metadata.lineage ?? {};
  if (tab === "structure") {
    return (
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Schema & privacy classification</Typography>
        <Typography className="body-emphasis">
          Each field carries an explicit privacy class so ingestion and retrieval policies can enforce minimisation.
        </Typography>
        <Table size="small">
          <TableHead><TableRow><TableCell>Field</TableCell><TableCell>Type</TableCell><TableCell>Privacy</TableCell><TableCell>Nullable</TableCell></TableRow></TableHead>
          <TableBody>
            {(metadata.schema ?? []).map((field: any) => (
              <TableRow key={field.name}>
                <TableCell><strong>{field.name}</strong></TableCell>
                <TableCell>{field.type}</TableCell>
                <TableCell><Chip size="small" variant="outlined" label={field.privacy.replaceAll("_", " ")} /></TableCell>
                <TableCell>{field.nullable ? "Yes" : "No"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    );
  }
  if (tab === "governance") {
    return (
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Quality evidence</Typography>
          <div className="metric-detail-grid">
            <LabelValue label="Overall quality" value={`${quality.overall_score}%`} />
            <LabelValue label="Completeness" value={`${quality.completeness}%`} />
            <LabelValue label="Duplicate rate" value={`${quality.duplicate_rate}%`} />
            <LabelValue label="Label agreement" value={`${quality.label_agreement}%`} />
            <LabelValue label="Freshness" value={`${quality.freshness_days} days`} />
            <LabelValue label="Last validation" value={new Date(quality.last_validation).toLocaleString()} />
          </div>
          <Divider />
          <Stack spacing={1}>
            {(metadata.controls ?? []).map((control: any) => (
              <div className="control-row" key={control.name}>
                <span className={control.status === "passed" ? "control-ok" : "control-attention"}>
                  {control.status === "passed" ? "OK" : "!"}
                </span>
                <div><strong>{control.name}</strong><small>{control.status}</small></div>
              </div>
            ))}
          </Stack>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Handling policy</Typography>
          <div className="metadata-grid top-gap">
            <LabelValue label="Classification" value={metadata.classification} />
            <LabelValue label="License" value={metadata.license} />
            <LabelValue label="Retention" value={metadata.retention} />
          </div>
        </Paper>
      </div>
    );
  }
  if (tab === "activity") return <Timeline detail={detail} />;
  return (
    <div className="detail-grid">
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Dataset contract</Typography>
        <Typography className="body-emphasis">{detail.asset.intended_use}</Typography>
        <div className="metric-detail-grid">
          <LabelValue label="Source" value={source.system} />
          <LabelValue label="Format" value={source.format} />
          <LabelValue label="Records" value={Number(source.record_count).toLocaleString()} />
          <LabelValue label="Refresh cadence" value={source.refresh_cadence} />
        </div>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Lineage</Typography>
        {Object.entries(lineage).map(([key, values]) => (
          <div key={key}>
            <Typography className="subsection-heading">{key}</Typography>
            <Stack direction="row" gap={1} flexWrap="wrap">
              {(values as string[]).map((value) => <Chip size="small" variant="outlined" key={value} label={value} />)}
            </Stack>
          </div>
        ))}
      </Paper>
    </div>
  );
}

function McpDetail({
  detail,
  tab,
  onRefresh,
  refreshing,
}: {
  detail: AssetDetail;
  tab: DetailTab;
  onRefresh: () => void;
  refreshing: boolean;
}) {
  const metadata = detail.metadata;
  const tools = detail.live_status?.tools ?? metadata.declared_tools?.map((name: string) => ({ name }));
  if (tab === "structure") {
    return (
      <Paper className="content-card">
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <div>
            <Typography className="section-heading" variant="h6">Discovered tools & schemas</Typography>
            <Typography variant="body2" color="text.secondary">Schemas come from a live MCP initialize/list-tools exchange when refreshed.</Typography>
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
            <LabelValue label="Authentication" value={metadata.auth?.method} />
            <LabelValue label="Default action" value={metadata.policy?.default_action} />
            <LabelValue label="Network zone" value={metadata.policy?.network_zone} />
            <LabelValue label="Secret storage" value={metadata.auth?.secret_storage} />
          </div>
          <Typography className="subsection-heading">Required roles</Typography>
          <Stack direction="row" gap={1}>{metadata.auth?.required_roles?.map((role: string) => <Chip key={role} label={role} size="small" />)}</Stack>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Human approval boundary</Typography>
          <Typography className="body-emphasis">
            High-impact tools remain denied unless the caller carries an authorised identity and the workflow supplies review evidence.
          </Typography>
          {(metadata.policy?.human_approval_for ?? []).map((item: string) => <Chip key={item} label={item.replaceAll("_", " ")} color="warning" size="small" sx={{ mr: 1 }} />)}
        </Paper>
      </div>
    );
  }
  if (tab === "activity") return <Timeline detail={detail} />;
  const live = detail.live_status;
  return (
    <div className="detail-grid">
      <Paper className="content-card">
        <Stack direction="row" justifyContent="space-between">
          <Typography className="section-heading" variant="h6">Protocol endpoint</Typography>
          <Chip
            size="small"
            color={live?.reachable ? "success" : live ? "error" : "default"}
            label={live?.reachable ? "Live" : live ? "Unavailable" : "Not checked"}
          />
        </Stack>
        <Typography className="body-emphasis">{metadata.endpoint}</Typography>
        <div className="metadata-grid">
          <LabelValue label="Transport" value={metadata.transport} />
          <LabelValue label="Exposure" value={metadata.exposure} />
          <LabelValue label="Declared protocol" value={metadata.protocol_version} />
          <LabelValue label="Negotiated protocol" value={live?.protocol_version} />
          <LabelValue label="Server" value={live?.server?.name} />
        </div>
        {live?.error && <Alert severity="warning" sx={{ mt: 2 }}>{live.error}</Alert>}
        <Button sx={{ mt: 2 }} variant="contained" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? "Discovering…" : "Run live discovery"}
        </Button>
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

function GenericDetail({ detail, tab }: { detail: AssetDetail; tab: DetailTab }) {
  if (tab === "activity") return <Timeline detail={detail} />;
  return (
    <Paper className="content-card">
      <Alert severity="info" sx={{ mb: 2 }}>
        This asset is governed through the shared registry contract. A type-specific operational module will be added when its real execution source is connected.
      </Alert>
      <Typography className="section-heading" variant="h6">Registry contract</Typography>
      <Typography className="body-emphasis">{detail.asset.intended_use}</Typography>
      <div className="metric-detail-grid">
        <LabelValue label="Owner" value={detail.asset.owner} />
        <LabelValue label="Asset type" value={detail.asset.asset_type} />
        <LabelValue label="Risk" value={detail.asset.risk_level} />
        <LabelValue label="Source commit" value={detail.asset.source_commit} />
        <LabelValue label="Created" value={new Date(detail.asset.created_at).toLocaleString()} />
        <LabelValue label="Updated" value={new Date(detail.asset.updated_at).toLocaleString()} />
      </div>
    </Paper>
  );
}

export function AssetDetailPage({
  assetId,
  version,
  onBack,
}: {
  assetId: string;
  version: string;
  onBack: (type: Asset["asset_type"]) => void;
}) {
  const [tab, setTab] = useState<DetailTab>("overview");
  const [refreshLive, setRefreshLive] = useState(false);
  const detail = useQuery({
    queryKey: ["asset-detail", assetId, version, refreshLive],
    queryFn: () => getAssetDetail(assetId, version, refreshLive),
  });
  if (detail.isPending) return <Paper className="loading-panel"><CircularProgress size={24} />Loading asset evidence…</Paper>;
  if (detail.isError) return <Alert severity="error">{detail.error.message}</Alert>;
  const data = detail.data;
  return (
    <>
      <button className="back-link" onClick={() => onBack(data.asset.asset_type)}>← Back to inventory</button>
      <section className="agent-hero">
        <div className="agent-avatar">{data.asset.asset_type === "dataset" ? "DS" : data.asset.asset_type === "mcp_server" ? "MC" : "AI"}</div>
        <div className="agent-title">
          <span>{data.detail_kind.replaceAll("_", " ")} · {data.asset.asset_id}</span>
          <Typography className="strong-heading" variant="h3">{data.asset.display_name}</Typography>
          <Typography color="text.secondary">{data.asset.intended_use}</Typography>
          <Stack direction="row" spacing={1} mt={1.5}>
            <StateChip asset={data.asset} />
            <Chip size="small" variant="outlined" label={`Risk: ${data.asset.risk_level}`} />
            <Chip size="small" variant="outlined" label={`v${data.asset.version}`} />
          </Stack>
        </div>
      </section>
      <Paper className="detail-tabs">
        <Tabs value={tab} onChange={(_, value: DetailTab) => setTab(value)} variant="scrollable">
          <Tab value="overview" label="Overview" />
          <Tab value="structure" label={data.asset.asset_type === "dataset" ? "Schema & privacy" : data.asset.asset_type === "mcp_server" ? "Tools & schemas" : "Structure"} />
          <Tab value="governance" label={data.asset.asset_type === "dataset" ? "Quality & controls" : "Governance"} />
          <Tab value="activity" label="Versions & audit" />
        </Tabs>
      </Paper>
      <div className="tab-content">
        {data.asset.asset_type === "dataset" ? (
          <DatasetDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "mcp_server" ? (
          <McpDetail detail={data} tab={tab} onRefresh={() => setRefreshLive(true)} refreshing={detail.isFetching} />
        ) : (
          <GenericDetail detail={data} tab={tab} />
        )}
      </div>
    </>
  );
}
