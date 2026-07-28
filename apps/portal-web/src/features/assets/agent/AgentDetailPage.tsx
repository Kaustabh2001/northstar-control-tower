import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";

import { getAgentDetail, requestApproval } from "../../../api";
import { useAuth } from "../../../auth";
import { LabelValue, LoadingPanel, StatusChip } from "../../../shared/components";
import type { AgentDetail, GovernanceState } from "../../../types";

type DetailTab = "overview" | "a2a" | "dependencies" | "governance" | "activity";

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
          <div><strong>{detail.health.status.replaceAll("_", " ")}</strong><small>A2A health probe has not been connected yet.</small></div>
        </div>
        <Divider />
        <LabelValue label="Runtime telemetry" value={detail.runtime_connected ? "Connected" : "Awaiting runtime slice"} />
      </Paper>
    </div>
  );
}

function A2ADetail({ detail }: { detail: AgentDetail }) {
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <div><Typography className="section-heading" variant="h6">A2A Agent Card</Typography><Typography variant="body2" color="text.secondary">The discoverable protocol contract exposed to workflows and peer agents.</Typography></div>
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
              <strong>{skill.name}</strong><p>{skill.description}</p>
              <Stack direction="row" gap={0.7} flexWrap="wrap">{skill.tags.map((tag) => <Chip key={tag} label={tag} size="small" />)}</Stack>
            </div>
          ))}
        </Stack>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Capabilities</Typography>
        <Stack spacing={1.2} mt={2}>
          {Object.entries(detail.agent_card.capabilities).map(([name, enabled]) => (
            <div className="capability-row" key={name}><strong>{name.replaceAll("_", " ")}</strong><Chip size="small" color={enabled ? "success" : "default"} label={enabled ? "Enabled" : "Disabled"} /></div>
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
      <Typography variant="body2" color="text.secondary">Models, datasets and tools this agent is authorised to use.</Typography>
      <div className="dependency-list">
        {detail.dependencies.map((dependency) => (
          <div className="dependency-card" key={dependency.asset_id}>
            <span>{dependency.asset_type.slice(0, 2).toUpperCase()}</span>
            <div><strong>{dependency.display_name}</strong><small>{dependency.asset_id} · {dependency.version}</small></div>
            <Chip size="small" variant="outlined" label={dependency.relationship.replaceAll("_", " ")} />
          </div>
        ))}
      </div>
    </Paper>
  );
}

function Governance({
  detail,
  onTransition,
}: {
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
              <span className={control.status === "implemented" ? "control-ok" : "control-attention"}>{control.status === "implemented" ? "OK" : "!"}</span>
              <div><strong>{control.name}</strong><small>{control.control_id} · {control.evidence}</small></div>
              <Chip size="small" label={control.status} />
            </div>
          ))}
        </Stack>
      </Paper>
      <Paper className="content-card decision-panel">
        <Typography className="section-heading" variant="h6">Lifecycle decision</Typography>
        <StatusChip asset={detail.asset} />
        <Typography variant="body2" color="text.secondary">Every transition is role-checked by the API and written to the audit trail.</Typography>
        {auth.hasRole("operator", "admin") && detail.asset.governance_state === "build_test" && <Button variant="contained" onClick={() => onTransition("steward_review", "Request steward review")}>Request steward review</Button>}
        {detail.asset.governance_state === "steward_review" && <Alert severity="info">A reviewer must decide the pending request in Lifecycle &amp; Approvals.</Alert>}
      </Paper>
    </div>
  );
}

function Activity({ detail }: { detail: AgentDetail }) {
  return (
    <div className="detail-grid">
      <Paper className="content-card detail-main">
        <Typography className="section-heading" variant="h6">Governance audit trail</Typography>
        <div className="timeline">{detail.audit_events.map((event) => <div className="timeline-item" key={event.event_id}><i /><div><strong>{event.action.replaceAll(".", " ")}</strong><p>{event.detail}</p><small>{event.actor_email} · {new Date(event.created_at).toLocaleString()}</small></div></div>)}</div>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Recent executions</Typography>
        <Alert severity="info" sx={{ mt: 2 }}>Workflow runs are available in Runtime Operations.</Alert>
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
        <Typography variant="body2" color="text.secondary" mb={2}>Add the evidence or decision rationale retained in the audit trail.</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField autoFocus fullWidth multiline minRows={3} label="Decision note" value={note} onChange={(event) => setNote(event.target.value)} />
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Cancel</Button><Button variant="contained" disabled={note.trim().length < 3 || pending} onClick={() => onSubmit(note)}>{pending ? "Recording…" : "Confirm decision"}</Button></DialogActions>
    </Dialog>
  );
}

export function AgentDetailPage({
  assetId,
  version,
  onBack,
}: {
  assetId: string;
  version: string;
  onBack: () => void;
}) {
  const [tab, setTab] = useState<DetailTab>("overview");
  const [transition, setTransition] = useState<{ state: GovernanceState; label: string } | null>(null);
  const queryClient = useQueryClient();
  const detail = useQuery({ queryKey: ["agent", assetId, version], queryFn: () => getAgentDetail(assetId, version) });
  const mutation = useMutation({
    mutationFn: ({ state, note }: { state: GovernanceState; note: string }) => requestApproval(assetId, version, state, note),
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
          <Typography className="strong-heading" variant="h3">{data.asset.display_name}</Typography>
          <Typography color="text.secondary">{data.agent_card.description}</Typography>
          <Stack direction="row" spacing={1} mt={1.5}><StatusChip asset={data.asset} /><Chip size="small" variant="outlined" label={`Risk: ${data.asset.risk_level}`} /><Chip size="small" variant="outlined" label={`v${data.asset.version}`} /></Stack>
        </div>
      </section>
      <Paper className="detail-tabs">
        <Tabs value={tab} onChange={(_, value: DetailTab) => setTab(value)} variant="scrollable" scrollButtons="auto">
          <Tab value="overview" label="Overview" /><Tab value="a2a" label="A2A card & skills" /><Tab value="dependencies" label="Dependencies" /><Tab value="governance" label="Governance" /><Tab value="activity" label="Runs & audit" />
        </Tabs>
      </Paper>
      <div className="tab-content">
        {tab === "overview" && <AgentOverview detail={data} />}
        {tab === "a2a" && <A2ADetail detail={data} />}
        {tab === "dependencies" && <Dependencies detail={data} />}
        {tab === "governance" && <Governance detail={data} onTransition={(state, label) => setTransition({ state, label })} />}
        {tab === "activity" && <Activity detail={data} />}
      </div>
      <TransitionDialog open={Boolean(transition)} label={transition?.label ?? ""} pending={mutation.isPending} error={mutation.isError ? mutation.error.message : undefined} onClose={() => setTransition(null)} onSubmit={(note) => transition && mutation.mutate({ state: transition.state, note })} />
    </>
  );
}
