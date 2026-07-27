import { FormEvent, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";

import {
  getAgentDetail,
  getAssets,
  getDashboard,
  registerAsset,
  transitionAgent,
} from "./api";
import { authMode, useAuth } from "./auth";
import type {
  AgentDetail,
  Asset,
  AssetType,
  GovernanceState,
  NewAsset,
} from "./types";

type Page = "overview" | "inventory" | "agent" | "lifecycle" | "runtime" | "security";
type AssetFilter = AssetType | "all";
type DetailTab = "overview" | "a2a" | "dependencies" | "governance" | "activity";

interface RouteState {
  page: Page;
  assetId?: string;
  version?: string;
}

const assetTypes: Array<{ value: AssetFilter; label: string; mark: string }> = [
  { value: "all", label: "All assets", mark: "AI" },
  { value: "ai_system", label: "AI systems", mark: "SY" },
  { value: "agentic_workflow", label: "Agentic workflows", mark: "WF" },
  { value: "agent", label: "Agents", mark: "AG" },
  { value: "model", label: "Models", mark: "ML" },
  { value: "prompt", label: "Prompts", mark: "PR" },
  { value: "dataset", label: "Datasets", mark: "DS" },
  { value: "knowledge_index", label: "Knowledge indexes", mark: "KB" },
  { value: "mcp_server", label: "MCP servers", mark: "MC" },
];

const typeLabels: Record<AssetFilter, string> = {
  all: "Asset",
  ai_system: "AI system",
  agentic_workflow: "Agentic workflow",
  agent: "Agent",
  model: "Model",
  prompt: "Prompt",
  dataset: "Dataset",
  knowledge_index: "Knowledge index",
  mcp_server: "MCP server",
};

const initialAsset: NewAsset = {
  asset_id: "",
  version: "0.1.0",
  asset_type: "agent",
  display_name: "",
  owner: "",
  intended_use: "",
};

function routeFromLocation(): RouteState {
  const match = window.location.pathname.match(
    /^\/assets\/([^/]+)\/versions\/([^/]+)$/,
  );
  if (match) {
    return {
      page: "agent",
      assetId: decodeURIComponent(match[1]),
      version: decodeURIComponent(match[2]),
    };
  }
  return { page: "overview" };
}

function StatusChip({ asset }: { asset: Asset }) {
  const color =
    asset.governance_state === "production"
      ? "success"
      : asset.governance_state === "steward_review"
        ? "warning"
        : "default";
  return (
    <Chip
      size="small"
      color={color}
      label={asset.governance_state.replaceAll("_", " ")}
      sx={{ textTransform: "capitalize", fontWeight: 800 }}
    />
  );
}

function LoadingPanel({ label = "Loading control-plane data…" }: { label?: string }) {
  return (
    <Paper className="loading-panel">
      <CircularProgress size={24} />
      <Typography color="text.secondary">{label}</Typography>
    </Paper>
  );
}

function LoginScreen() {
  const auth = useAuth();
  if (auth.loading) return <div className="login-shell"><CircularProgress /></div>;
  return (
    <div className="login-shell">
      <Paper className="login-card">
        <span className="brand-mark large">NS</span>
        <Typography className="strong-heading" variant="h3">
          Govern every AI decision.
        </Typography>
        <Typography color="text.secondary">
          Sign in to the Northstar control plane to inspect assets, evidence,
          lifecycle decisions and runtime accountability.
        </Typography>
        <Button variant="contained" size="large" onClick={() => void auth.login()}>
          Sign in with Keycloak
        </Button>
        <div className="login-note">
          <strong>Local demonstration</strong>
          <span>admin@northstar.local / northstar</span>
        </div>
      </Paper>
    </div>
  );
}

function Sidebar({
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
              className={
                page === value || (value === "inventory" && page === "agent")
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() => onNavigate(value)}
            >
              <span className="nav-mark">{mark}</span><strong>{label}</strong>
            </button>
            {value === "inventory" && (
              <div className="asset-subnav">
                {assetTypes.map((type) => (
                  <button
                    key={type.value}
                    className={
                      (page === "inventory" || page === "agent")
                      && assetFilter === type.value
                        ? "active"
                        : ""
                    }
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

function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <span>{eyebrow}</span>
        <Typography className="strong-heading" variant="h3">{title}</Typography>
        <Typography color="text.secondary">{description}</Typography>
      </div>
      {action}
    </header>
  );
}

function Overview({ onRegister }: { onRegister: () => void }) {
  const summary = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  if (summary.isPending) return <LoadingPanel />;
  if (summary.isError) return <Alert severity="error">{summary.error.message}</Alert>;
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
        description="Live registry data from the secured FastAPI control plane."
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

function Inventory({
  assetFilter,
  onFilter,
  onRegister,
  onOpen,
}: {
  assetFilter: AssetFilter;
  onFilter: (value: AssetFilter) => void;
  onRegister: () => void;
  onOpen: (asset: Asset) => void;
}) {
  const [query, setQuery] = useState("");
  const assets = useQuery({
    queryKey: ["assets", assetFilter, query],
    queryFn: () => getAssets(assetFilter, query),
  });
  return (
    <>
      <PageHeader
        eyebrow="Governed portfolio"
        title={
          assetFilter === "all"
            ? "All AI assets"
            : assetTypes.find((type) => type.value === assetFilter)!.label
        }
        description="Open an agent to inspect its A2A contract, controls, dependencies and decisions."
        action={<Button variant="contained" onClick={onRegister}>Register asset</Button>}
      />
      <Paper className="content-card">
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} mb={2}>
          <TextField
            size="small"
            fullWidth
            label="Search name, ID or owner"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <FormControl size="small" sx={{ minWidth: 210 }}>
            <InputLabel>Asset type</InputLabel>
            <Select
              value={assetFilter}
              label="Asset type"
              onChange={(event) => onFilter(event.target.value as AssetFilter)}
            >
              {assetTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
        {assets.isError && <Alert severity="error">{assets.error.message}</Alert>}
        {assets.isPending ? <LoadingPanel /> : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Asset</TableCell><TableCell>Type</TableCell>
                  <TableCell>Governance state</TableCell><TableCell>Risk</TableCell>
                  <TableCell>Owner</TableCell><TableCell>Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assets.data?.map((asset) => (
                  <TableRow
                    key={`${asset.asset_id}:${asset.version}`}
                    hover
                    className={asset.asset_type === "agent" ? "clickable-row" : ""}
                    tabIndex={asset.asset_type === "agent" ? 0 : -1}
                    onClick={() => asset.asset_type === "agent" && onOpen(asset)}
                    onKeyDown={(event) => {
                      if (
                        asset.asset_type === "agent"
                        && (event.key === "Enter" || event.key === " ")
                      ) onOpen(asset);
                    }}
                  >
                    <TableCell>
                      <div className="asset-name">
                        <span>{assetTypes.find((type) => type.value === asset.asset_type)?.mark}</span>
                        <div>
                          <strong>{asset.display_name}</strong>
                          <small>{asset.asset_id} · {asset.version}</small>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell><strong>{typeLabels[asset.asset_type]}</strong></TableCell>
                    <TableCell><StatusChip asset={asset} /></TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        variant="outlined"
                        label={asset.risk_level}
                        sx={{ textTransform: "capitalize", fontWeight: 700 }}
                      />
                    </TableCell>
                    <TableCell>{asset.owner}</TableCell>
                    <TableCell>{new Date(asset.updated_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
                {!assets.data?.length && (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <Typography color="text.secondary" textAlign="center" py={4}>
                        No assets match this filter.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </>
  );
}

function LabelValue({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="label-value">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function AgentOverview({ detail }: { detail: AgentDetail }) {
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Typography className="section-heading" variant="h6">Purpose and accountability</Typography>
        <Typography className="body-emphasis">{detail.asset.intended_use}</Typography>
        <Divider />
        <div className="metadata-grid">
          <LabelValue label="Accountable owner" value={detail.asset.owner} />
          <LabelValue label="Risk classification" value={detail.asset.risk_level} />
          <LabelValue label="Source commit" value={detail.asset.source_commit ?? "Not supplied"} />
          <LabelValue label="Registered version" value={detail.asset.version} />
        </div>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Operational readiness</Typography>
        <div className="readiness-block">
          <span className={`health-dot ${detail.health.status}`} />
          <div>
            <strong>{detail.health.status.replaceAll("_", " ")}</strong>
            <small>A2A health probe has not been connected yet.</small>
          </div>
        </div>
        <Divider />
        <LabelValue
          label="Runtime telemetry"
          value={detail.runtime_connected ? "Connected" : "Awaiting runtime slice"}
        />
      </Paper>
    </div>
  );
}

function A2ADetail({ detail }: { detail: AgentDetail }) {
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <div>
            <Typography className="section-heading" variant="h6">A2A Agent Card</Typography>
            <Typography variant="body2" color="text.secondary">
              The discoverable protocol contract exposed to workflows and peer agents.
            </Typography>
          </div>
          <Chip label={`A2A ${detail.agent_card.protocol_version}`} color="success" />
        </Stack>
        <div className="metadata-grid top-gap">
          <LabelValue label="Endpoint" value={detail.agent_card.url} />
          <LabelValue label="Preferred transport" value={detail.agent_card.preferred_transport} />
        </div>
        <Divider />
        <Typography className="subsection-heading">Declared skills</Typography>
        <Stack spacing={1.5}>
          {detail.agent_card.skills.map((skill) => (
            <div className="skill-card" key={skill.skill_id}>
              <strong>{skill.name}</strong>
              <p>{skill.description}</p>
              <Stack direction="row" gap={0.7} flexWrap="wrap">
                {skill.tags.map((tag) => <Chip key={tag} label={tag} size="small" />)}
              </Stack>
            </div>
          ))}
        </Stack>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Capabilities</Typography>
        <Stack spacing={1.2} mt={2}>
          {Object.entries(detail.agent_card.capabilities).map(([name, enabled]) => (
            <div className="capability-row" key={name}>
              <strong>{name.replaceAll("_", " ")}</strong>
              <Chip
                size="small"
                color={enabled ? "success" : "default"}
                label={enabled ? "Enabled" : "Disabled"}
              />
            </div>
          ))}
        </Stack>
      </Paper>
    </div>
  );
}

function Dependencies({ detail }: { detail: AgentDetail }) {
  return (
    <Paper className="content-card">
      <Typography className="section-heading" variant="h6">Governed dependency graph</Typography>
      <Typography variant="body2" color="text.secondary">
        Models, datasets and tools this agent is authorised to use.
      </Typography>
      <div className="dependency-list">
        {detail.dependencies.map((dependency) => (
          <div className="dependency-card" key={dependency.asset_id}>
            <span>{dependency.asset_type.slice(0, 2).toUpperCase()}</span>
            <div>
              <strong>{dependency.display_name}</strong>
              <small>{dependency.asset_id} · {dependency.version}</small>
            </div>
            <Chip size="small" variant="outlined" label={dependency.relationship.replaceAll("_", " ")} />
          </div>
        ))}
      </div>
    </Paper>
  );
}

function Governance({ detail, onTransition }: {
  detail: AgentDetail;
  onTransition: (state: GovernanceState, label: string) => void;
}) {
  const auth = useAuth();
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Typography className="section-heading" variant="h6">Control evidence</Typography>
        <Stack spacing={1.2} mt={2}>
          {detail.controls.map((control) => (
            <div className="control-row" key={control.control_id}>
              <span className={control.status === "implemented" ? "control-ok" : "control-attention"}>
                {control.status === "implemented" ? "OK" : "!"}
              </span>
              <div>
                <strong>{control.name}</strong>
                <small>{control.control_id} · {control.evidence}</small>
              </div>
              <Chip size="small" label={control.status} />
            </div>
          ))}
        </Stack>
      </Paper>
      <Paper className="content-card decision-panel">
        <Typography className="section-heading" variant="h6">Lifecycle decision</Typography>
        <StatusChip asset={detail.asset} />
        <Typography variant="body2" color="text.secondary">
          Every transition is role-checked by the API and written to the audit trail.
        </Typography>
        {auth.hasRole("operator", "admin") && detail.asset.governance_state !== "steward_review" && (
          <Button
            variant="contained"
            onClick={() => onTransition("steward_review", "Submit for steward review")}
          >
            Submit for steward review
          </Button>
        )}
        {auth.hasRole("reviewer", "admin") && detail.asset.governance_state === "steward_review" && (
          <Button
            variant="contained"
            color="success"
            onClick={() => onTransition("shadow", "Approve for shadow operation")}
          >
            Approve for shadow
          </Button>
        )}
        {auth.hasRole("admin") && (
          <Button
            variant="outlined"
            color="error"
            onClick={() => onTransition("retired", "Retire agent version")}
          >
            Retire version
          </Button>
        )}
      </Paper>
    </div>
  );
}

function Activity({ detail }: { detail: AgentDetail }) {
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Typography className="section-heading" variant="h6">Governance audit trail</Typography>
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
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Recent executions</Typography>
        <Alert severity="info" sx={{ mt: 2 }}>
          No runtime source is connected. LangGraph runs and traces will appear here after the Runtime Operations slice.
        </Alert>
      </Paper>
    </div>
  );
}

function TransitionDialog({
  open,
  label,
  pending,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  label: string;
  pending: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (note: string) => void;
}) {
  const [note, setNote] = useState("");
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle className="strong-heading">{label}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Add the evidence or decision rationale that should be retained in the audit trail.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          autoFocus
          fullWidth
          multiline
          minRows={3}
          label="Decision note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={note.trim().length < 3 || pending}
          onClick={() => onSubmit(note)}
        >
          {pending ? "Recording…" : "Confirm decision"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function AgentDetailPage({
  assetId,
  version,
  onBack,
}: {
  assetId: string;
  version: string;
  onBack: () => void;
}) {
  const [tab, setTab] = useState<DetailTab>("overview");
  const [transition, setTransition] = useState<{
    state: GovernanceState;
    label: string;
  } | null>(null);
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ["agent", assetId, version],
    queryFn: () => getAgentDetail(assetId, version),
  });
  const mutation = useMutation({
    mutationFn: ({ state, note }: { state: GovernanceState; note: string }) =>
      transitionAgent(assetId, version, state, note),
    onSuccess: async () => {
      setTransition(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["agent", assetId, version] }),
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });
  if (detail.isPending) return <LoadingPanel label="Loading governed agent record…" />;
  if (detail.isError) return <Alert severity="error">{detail.error.message}</Alert>;
  const data = detail.data;
  return (
    <>
      <button className="back-link" onClick={onBack}>← Back to agent inventory</button>
      <section className="agent-hero">
        <div className="agent-avatar">AG</div>
        <div className="agent-title">
          <span>Governed agent · {data.asset.asset_id}</span>
          <Typography className="strong-heading" variant="h3">
            {data.asset.display_name}
          </Typography>
          <Typography color="text.secondary">{data.agent_card.description}</Typography>
          <Stack direction="row" spacing={1} mt={1.5}>
            <StatusChip asset={data.asset} />
            <Chip size="small" variant="outlined" label={`Risk: ${data.asset.risk_level}`} />
            <Chip size="small" variant="outlined" label={`v${data.asset.version}`} />
          </Stack>
        </div>
      </section>
      <Paper className="detail-tabs">
        <Tabs
          value={tab}
          onChange={(_, value: DetailTab) => setTab(value)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab value="overview" label="Overview" />
          <Tab value="a2a" label="A2A card & skills" />
          <Tab value="dependencies" label="Dependencies" />
          <Tab value="governance" label="Governance" />
          <Tab value="activity" label="Runs & audit" />
        </Tabs>
      </Paper>
      <div className="tab-content">
        {tab === "overview" && <AgentOverview detail={data} />}
        {tab === "a2a" && <A2ADetail detail={data} />}
        {tab === "dependencies" && <Dependencies detail={data} />}
        {tab === "governance" && (
          <Governance
            detail={data}
            onTransition={(state, label) => setTransition({ state, label })}
          />
        )}
        {tab === "activity" && <Activity detail={data} />}
      </div>
      <TransitionDialog
        open={Boolean(transition)}
        label={transition?.label ?? ""}
        pending={mutation.isPending}
        error={mutation.isError ? mutation.error.message : undefined}
        onClose={() => setTransition(null)}
        onSubmit={(note) => transition && mutation.mutate({ state: transition.state, note })}
      />
    </>
  );
}

function PlannedPage({ page }: { page: Exclude<Page, "overview" | "inventory" | "agent"> }) {
  const copy = {
    lifecycle: ["Asset governance lifecycle", "Evidence approvals and portfolio transition queues build on the secured agent decisions now in place."],
    runtime: ["Runtime operations", "Workflow runs, LangGraph checkpoints, traces and human review are the next implementation slice."],
    security: ["Security & privacy", "Keycloak identity is active; gateway enforcement and privacy events follow with ContextForge."],
  }[page];
  return (
    <>
      <PageHeader eyebrow="Next integration slice" title={copy[0]} description={copy[1]} />
      <Paper className="planned-card">
        <span>SECURED FOUNDATION</span>
        <Typography className="strong-heading" variant="h5">The control plane has an accountable identity boundary.</Typography>
        <Typography color="text.secondary">
          This page will be populated only when its real event source and enforcement path are implemented.
        </Typography>
      </Paper>
    </>
  );
}

function RegisterDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [asset, setAsset] = useState<NewAsset>(initialAsset);
  const mutation = useMutation({
    mutationFn: registerAsset,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
      setAsset(initialAsset);
      onClose();
    },
  });
  const valid = useMemo(
    () => Object.values(asset).every((value) => value.trim()),
    [asset],
  );
  function update<K extends keyof NewAsset>(key: K, value: NewAsset[K]) {
    setAsset((current) => ({ ...current, [key]: value }));
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    if (valid) mutation.mutate(asset);
  }
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <Box component="form" onSubmit={submit}>
        <DialogTitle className="strong-heading">Register governed asset</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Create a versioned registry record attributed to your signed-in identity.
          </Typography>
          <Stack spacing={2}>
            {mutation.isError && <Alert severity="error">{mutation.error.message}</Alert>}
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField required fullWidth label="Asset ID" placeholder="agent.policy-risk" value={asset.asset_id} onChange={(event) => update("asset_id", event.target.value)} />
              <TextField required label="Version" value={asset.version} onChange={(event) => update("version", event.target.value)} />
            </Stack>
            <TextField required label="Display name" value={asset.display_name} onChange={(event) => update("display_name", event.target.value)} />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Asset type</InputLabel>
                <Select value={asset.asset_type} label="Asset type" onChange={(event) => update("asset_type", event.target.value as AssetType)}>
                  {assetTypes.filter((type) => type.value !== "all").map((type) => (
                    <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField required fullWidth label="Owner" value={asset.owner} onChange={(event) => update("owner", event.target.value)} />
            </Stack>
            <TextField required multiline minRows={3} label="Intended use" value={asset.intended_use} onChange={(event) => update("intended_use", event.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={!valid || mutation.isPending}>
            {mutation.isPending ? "Registering…" : "Register asset"}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
}

export function App() {
  const auth = useAuth();
  const [route, setRoute] = useState<RouteState>(routeFromLocation);
  const [assetFilter, setAssetFilter] = useState<AssetFilter>("all");
  const [registerOpen, setRegisterOpen] = useState(false);

  useEffect(() => {
    const onPopState = () => setRoute(routeFromLocation());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  function navigate(page: Page) {
    const path = page === "overview" ? "/" : `/${page}`;
    window.history.pushState({}, "", path);
    setRoute({ page });
  }
  function chooseAssetFilter(type: AssetFilter) {
    setAssetFilter(type);
    window.history.pushState({}, "", "/inventory");
    setRoute({ page: "inventory" });
  }
  function openAsset(asset: Asset) {
    const path = `/assets/${encodeURIComponent(asset.asset_id)}/versions/${encodeURIComponent(asset.version)}`;
    window.history.pushState({}, "", path);
    setAssetFilter("agent");
    setRoute({ page: "agent", assetId: asset.asset_id, version: asset.version });
  }

  if (auth.loading || !auth.authenticated) return <LoginScreen />;

  return (
    <div className="app-shell">
      <Sidebar
        page={route.page}
        assetFilter={assetFilter}
        onNavigate={navigate}
        onAssetFilter={chooseAssetFilter}
      />
      <main>
        <div className="topbar">
          <span>Workspace / <strong>Enterprise AI</strong></span>
          <Stack direction="row" alignItems="center" spacing={1.2}>
            <Chip
              size="small"
              color="success"
              variant="outlined"
              label={`${authMode() === "keycloak" ? "Keycloak" : "Fixture"} · secured`}
            />
            <div className="user-summary">
              <strong>{auth.user?.display_name}</strong>
              <small>{auth.user?.roles.join(" · ")}</small>
            </div>
            <Button size="small" onClick={auth.logout}>Sign out</Button>
          </Stack>
        </div>
        <div className="page-content">
          {route.page === "overview" && <Overview onRegister={() => setRegisterOpen(true)} />}
          {route.page === "inventory" && (
            <Inventory
              assetFilter={assetFilter}
              onFilter={chooseAssetFilter}
              onRegister={() => setRegisterOpen(true)}
              onOpen={openAsset}
            />
          )}
          {route.page === "agent" && route.assetId && route.version && (
            <AgentDetailPage
              assetId={route.assetId}
              version={route.version}
              onBack={() => chooseAssetFilter("agent")}
            />
          )}
          {!["overview", "inventory", "agent"].includes(route.page) && (
            <PlannedPage page={route.page as Exclude<Page, "overview" | "inventory" | "agent">} />
          )}
        </div>
      </main>
      <RegisterDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </div>
  );
}
