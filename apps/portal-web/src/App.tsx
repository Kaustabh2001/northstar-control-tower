import { FormEvent, useMemo, useState } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import { getAssets, getDashboard, registerAsset } from "./api";
import type { Asset, AssetType, NewAsset } from "./types";

type Page = "overview" | "inventory" | "lifecycle" | "runtime" | "security";
type AssetFilter = AssetType | "all";

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
      sx={{ textTransform: "capitalize", fontWeight: 700 }}
    />
  );
}

function LoadingPanel() {
  return (
    <Paper className="loading-panel">
      <CircularProgress size={24} />
      <Typography color="text.secondary">Loading control-plane data…</Typography>
    </Paper>
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
              className={page === value ? "nav-button active" : "nav-button"}
              onClick={() => onNavigate(value)}
            >
              <span className="nav-mark">{mark}</span>{label}
            </button>
            {value === "inventory" && (
              <div className="asset-subnav">
                {assetTypes.map((type) => (
                  <button
                    key={type.value}
                    className={page === "inventory" && assetFilter === type.value ? "active" : ""}
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
        description="Live registry data from the FastAPI control plane."
        action={<Button variant="contained" onClick={onRegister}>Register asset</Button>}
      />
      <div className="stat-grid">
        {stats.map(([label, value, note, mark]) => (
          <Paper className="stat-card" key={label}>
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <span className="stat-mark">{mark}</span>
            </Stack>
            <strong>{value}</strong>
            <Typography variant="caption" color="text.secondary">{note}</Typography>
          </Paper>
        ))}
      </div>
      <div className="overview-grid">
        <Paper className="content-card">
          <Typography variant="h6">Asset composition</Typography>
          <Typography variant="body2" color="text.secondary">Persisted versions grouped by governed type.</Typography>
          <div className="composition">
            {Object.entries(data.by_type).map(([type, count]) => (
              <div className="composition-row" key={type}>
                <span>{typeLabels[type as AssetFilter] ?? type}</span>
                <div><i style={{ width: `${Math.max(12, count * 16)}%` }} /></div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </Paper>
        <Paper className="content-card decision-card">
          <Chip size="small" color="warning" label={`${data.awaiting_review} waiting`} />
          <Typography variant="h6">Registry decisions</Typography>
          <Typography variant="body2" color="text.secondary">
            Asset versions in steward review cannot move to shadow or production until their evidence gate passes.
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
}: {
  assetFilter: AssetFilter;
  onFilter: (value: AssetFilter) => void;
  onRegister: () => void;
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
        title={assetFilter === "all" ? "All AI assets" : assetTypes.find((type) => type.value === assetFilter)!.label}
        description="Each row is a persisted, versioned governance record."
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
              {assetTypes.map((type) => <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>)}
            </Select>
          </FormControl>
        </Stack>
        {assets.isError && <Alert severity="error">{assets.error.message}</Alert>}
        {assets.isPending ? <LoadingPanel /> : (
          <TableContainer>
            <Table size="small">
              <TableHead><TableRow><TableCell>Asset</TableCell><TableCell>Type</TableCell><TableCell>Governance state</TableCell><TableCell>Risk</TableCell><TableCell>Owner</TableCell><TableCell>Updated</TableCell></TableRow></TableHead>
              <TableBody>
                {assets.data?.map((asset) => (
                  <TableRow key={`${asset.asset_id}:${asset.version}`} hover>
                    <TableCell><div className="asset-name"><span>{assetTypes.find((type) => type.value === asset.asset_type)?.mark}</span><div><strong>{asset.display_name}</strong><small>{asset.asset_id} · {asset.version}</small></div></div></TableCell>
                    <TableCell>{typeLabels[asset.asset_type]}</TableCell>
                    <TableCell><StatusChip asset={asset} /></TableCell>
                    <TableCell><Chip size="small" variant="outlined" label={asset.risk_level} sx={{ textTransform: "capitalize" }} /></TableCell>
                    <TableCell>{asset.owner}</TableCell>
                    <TableCell>{new Date(asset.updated_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
                {!assets.data?.length && <TableRow><TableCell colSpan={6}><Typography color="text.secondary" textAlign="center" py={4}>No assets match this filter.</Typography></TableCell></TableRow>}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </>
  );
}

function PlannedPage({ page }: { page: Exclude<Page, "overview" | "inventory"> }) {
  const copy = {
    lifecycle: ["Asset governance lifecycle", "Registry transition APIs and evidence approvals are the next backend slice."],
    runtime: ["Runtime operations", "Workflow run ingestion, LangGraph checkpoints and human review will connect after registry persistence."],
    security: ["Security & privacy", "Gateway enforcement events will be added with ContextForge and Keycloak integration."],
  }[page];
  return (
    <>
      <PageHeader eyebrow="Next integration slice" title={copy[0]} description={copy[1]} />
      <Paper className="planned-card">
        <span>FOUNDATION READY</span>
        <Typography variant="h5">The navigation contract is stable.</Typography>
        <Typography color="text.secondary">
          This page is intentionally not populated with fake production data. Its backend event source will be implemented in the named milestone.
        </Typography>
      </Paper>
    </>
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
      <div><span>{eyebrow}</span><Typography variant="h3">{title}</Typography><Typography color="text.secondary">{description}</Typography></div>
      {action}
    </header>
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
  const valid = useMemo(() => Object.values(asset).every((value) => value.trim()), [asset]);
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
        <DialogTitle>Register governed asset</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>Create a versioned registry record. Agent Cards and discovery will automate this later.</Typography>
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
                  {assetTypes.filter((type) => type.value !== "all").map((type) => <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>)}
                </Select>
              </FormControl>
              <TextField required fullWidth label="Owner" value={asset.owner} onChange={(event) => update("owner", event.target.value)} />
            </Stack>
            <TextField required multiline minRows={3} label="Intended use" value={asset.intended_use} onChange={(event) => update("intended_use", event.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={onClose}>Cancel</Button><Button type="submit" variant="contained" disabled={!valid || mutation.isPending}>{mutation.isPending ? "Registering…" : "Register asset"}</Button></DialogActions>
      </Box>
    </Dialog>
  );
}

export function App() {
  const [page, setPage] = useState<Page>("overview");
  const [assetFilter, setAssetFilter] = useState<AssetFilter>("all");
  const [registerOpen, setRegisterOpen] = useState(false);
  function chooseAssetFilter(type: AssetFilter) {
    setAssetFilter(type);
    setPage("inventory");
  }
  return (
    <div className="app-shell">
      <Sidebar page={page} assetFilter={assetFilter} onNavigate={setPage} onAssetFilter={chooseAssetFilter} />
      <main>
        <div className="topbar"><span>Workspace / <strong>Enterprise AI</strong></span><Chip size="small" color="success" variant="outlined" label="Local · API connected" /></div>
        <div className="page-content">
          {page === "overview" && <Overview onRegister={() => setRegisterOpen(true)} />}
          {page === "inventory" && <Inventory assetFilter={assetFilter} onFilter={chooseAssetFilter} onRegister={() => setRegisterOpen(true)} />}
          {page !== "overview" && page !== "inventory" && <PlannedPage page={page} />}
        </div>
      </main>
      <RegisterDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </div>
  );
}
