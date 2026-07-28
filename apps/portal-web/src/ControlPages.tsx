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
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import {
  decideApproval,
  decideHumanReview,
  getGovernancePortfolio,
  getMcpInvocations,
  getRunDetail,
  getRuntimePortfolio,
} from "./api";
import { useAuth } from "./auth";
import type {
  GovernanceApproval,
  HumanReview,
  RunDetail,
  WorkflowRun,
} from "./types";

function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <header className="page-header">
      <div>
        <span>{eyebrow}</span>
        <Typography className="strong-heading" variant="h3">{title}</Typography>
        <Typography color="text.secondary">{description}</Typography>
      </div>
    </header>
  );
}

function Loading() {
  return <Paper className="loading-panel"><LinearProgress sx={{ width: 220 }} /></Paper>;
}

function DecisionDialog({
  title,
  open,
  pending,
  onClose,
  onSubmit,
}: {
  title: string;
  open: boolean;
  pending: boolean;
  onClose: () => void;
  onSubmit: (note: string) => void;
}) {
  const [note, setNote] = useState("");
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle className="strong-heading">{title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          This rationale is retained with the accountable identity and decision.
        </Typography>
        <TextField fullWidth multiline minRows={3} label="Decision rationale" value={note} onChange={(event) => setNote(event.target.value)} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={note.trim().length < 3 || pending} onClick={() => onSubmit(note)}>
          Record decision
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export function GovernancePage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [decision, setDecision] = useState<{ approval: GovernanceApproval; value: "approve" | "reject" } | null>(null);
  const portfolio = useQuery({ queryKey: ["governance"], queryFn: getGovernancePortfolio });
  const mutation = useMutation({
    mutationFn: ({ approvalId, value, note }: { approvalId: string; value: "approve" | "reject"; note: string }) =>
      decideApproval(approvalId, value, note),
    onSuccess: async () => {
      setDecision(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["governance"] }),
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });
  if (portfolio.isPending) return <Loading />;
  if (portfolio.isError) return <Alert severity="error">{portfolio.error.message}</Alert>;
  const data = portfolio.data;
  const pending = data.approvals.filter((approval) => approval.status === "pending");
  return (
    <>
      <PageHeader
        eyebrow="Policy-driven governance"
        title="Lifecycle decisions with evidence."
        description="Every asset type follows explicit transitions, evidence gates and accountable approvals."
      />
      <div className="stat-grid governance-stats">
        {[
          ["Pending approvals", pending.length, "Reviewer action required"],
          ["Evidence records", data.evidence.length, "Version-bound artefacts"],
          ["Production assets", data.state_counts.production ?? 0, "Actively governed"],
          ["Suspended assets", data.state_counts.suspended ?? 0, "Runtime access denied"],
        ].map(([label, value, note]) => (
          <Paper className="stat-card" key={label}>
            <Typography className="metric-label" variant="caption">{label}</Typography>
            <strong>{value}</strong>
            <Typography variant="caption" color="text.secondary">{note}</Typography>
          </Paper>
        ))}
      </div>
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Approval queue</Typography>
          <Typography variant="body2" color="text.secondary">Decisions advance the registered version only after its evidence gate is satisfied.</Typography>
          <div className="approval-list">
            {pending.map((approval) => (
              <div className="approval-card" key={approval.approval_id}>
                <div>
                  <span>{approval.asset_type.replaceAll("_", " ")}</span>
                  <strong>{approval.display_name}</strong>
                  <small>{approval.current_state.replaceAll("_", " ")} → {approval.target_state.replaceAll("_", " ")}</small>
                  <p>{approval.request_note}</p>
                  <small>Requested by {approval.requested_by}</small>
                </div>
                {auth.hasRole("reviewer", "admin") && (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" color="error" onClick={() => setDecision({ approval, value: "reject" })}>Reject</Button>
                    <Button size="small" variant="contained" onClick={() => setDecision({ approval, value: "approve" })}>Approve</Button>
                  </Stack>
                )}
              </div>
            ))}
            {!pending.length && <Alert severity="success" sx={{ mt: 2 }}>No approvals are waiting.</Alert>}
          </div>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Evidence inventory</Typography>
          <div className="evidence-list">
            {data.evidence.map((evidence) => (
              <div key={evidence.evidence_id}>
                <Chip size="small" color={evidence.status === "accepted" ? "success" : "default"} label={evidence.status} />
                <strong>{evidence.title}</strong>
                <small>{evidence.evidence_type.replaceAll("_", " ")} · {evidence.asset_id}</small>
              </div>
            ))}
          </div>
        </Paper>
      </div>
      <DecisionDialog
        open={Boolean(decision)}
        title={`${decision?.value === "approve" ? "Approve" : "Reject"} ${decision?.approval.display_name ?? ""}`}
        pending={mutation.isPending}
        onClose={() => setDecision(null)}
        onSubmit={(note) => decision && mutation.mutate({ approvalId: decision.approval.approval_id, value: decision.value, note })}
      />
    </>
  );
}

function RunStatus({ status }: { status: string }) {
  const color = status === "completed" ? "success" : status === "failed" ? "error" : status === "waiting_for_human" ? "warning" : "info";
  return <Chip size="small" color={color} label={status.replaceAll("_", " ")} sx={{ textTransform: "capitalize", fontWeight: 800 }} />;
}

function RunDrawer({ detail, onClose }: { detail: RunDetail; onClose: () => void }) {
  return (
    <Paper className="run-detail-panel">
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
        <div>
          <Typography className="section-heading" variant="h6">Run {detail.run.run_id.slice(0, 8)}</Typography>
          <Typography variant="body2" color="text.secondary">{detail.run.correlation.trace_id}</Typography>
        </div>
        <Button size="small" onClick={onClose}>Close</Button>
      </Stack>
      <div className="stage-track">
        {detail.run.stages.map((stage, index) => (
          <div className={`stage-step stage-${stage.status}`} key={stage.stage_id}>
            <span>{index + 1}</span>
            <div><strong>{stage.display_name}</strong><small>{stage.status.replaceAll("_", " ")} · {stage.kind}</small></div>
          </div>
        ))}
      </div>
      {detail.run.error_summary && <Alert severity="error">{detail.run.error_code}: {detail.run.error_summary}</Alert>}
      <Divider sx={{ my: 2 }} />
      <Typography className="subsection-heading">Trace events</Typography>
      <div className="timeline">
        {detail.events.map((event) => (
          <div className="timeline-item" key={event.event_id}>
            <i /><div><strong>{event.event_type.replaceAll(".", " ")}</strong><p>{event.stage_id ?? "workflow"}</p><small>{event.actor_id} · {new Date(event.occurred_at).toLocaleString()}</small></div>
          </div>
        ))}
      </div>
    </Paper>
  );
}

export function RuntimePage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [reviewDecision, setReviewDecision] = useState<{ review: HumanReview; value: "approve" | "reject" } | null>(null);
  const runtime = useQuery({ queryKey: ["runtime"], queryFn: getRuntimePortfolio });
  const detail = useQuery({
    queryKey: ["run-detail", selectedRun],
    queryFn: () => getRunDetail(selectedRun!),
    enabled: Boolean(selectedRun),
  });
  const mutation = useMutation({
    mutationFn: ({ reviewId, value, note }: { reviewId: string; value: "approve" | "reject"; note: string }) =>
      decideHumanReview(reviewId, value, note),
    onSuccess: async (result) => {
      setReviewDecision(null);
      setSelectedRun(result.run.run_id);
      await queryClient.invalidateQueries({ queryKey: ["runtime"] });
      queryClient.setQueryData(["run-detail", result.run.run_id], result);
    },
  });
  if (runtime.isPending) return <Loading />;
  if (runtime.isError) return <Alert severity="error">{runtime.error.message}</Alert>;
  const pendingReviews = runtime.data.reviews.filter((review) => review.status === "pending");
  return (
    <>
      <PageHeader
        eyebrow="Live workflow accountability"
        title="Runtime operations."
        description="Follow each workflow stage, inspect correlated events and resolve human-review pauses."
      />
      <div className="runtime-layout">
        <div>
          <Paper className="content-card">
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <div><Typography className="section-heading" variant="h6">Workflow runs</Typography><Typography variant="body2" color="text.secondary">Persistent local run state and LangGraph-ready checkpoints.</Typography></div>
              <Stack direction="row" spacing={1}>{Object.entries(runtime.data.status_counts).map(([status, count]) => <Chip key={status} size="small" label={`${status.replaceAll("_", " ")} ${count}`} />)}</Stack>
            </Stack>
            <Table size="small">
              <TableHead><TableRow><TableCell>Run</TableCell><TableCell>Status</TableCell><TableCell>Current stage</TableCell><TableCell>Updated</TableCell></TableRow></TableHead>
              <TableBody>{runtime.data.runs.map((run: WorkflowRun) => (
                <TableRow className="clickable-row" hover key={run.run_id} onClick={() => setSelectedRun(run.run_id)}>
                  <TableCell><strong>{run.workflow_name}</strong><br /><small>{run.run_id.slice(0, 8)} · v{run.workflow_version}</small></TableCell>
                  <TableCell><RunStatus status={run.status} /></TableCell>
                  <TableCell>{run.current_stage_id?.replaceAll("-", " ")}</TableCell>
                  <TableCell>{new Date(run.updated_at).toLocaleTimeString()}</TableCell>
                </TableRow>
              ))}</TableBody>
            </Table>
          </Paper>
          {detail.isPending && selectedRun && <Loading />}
          {detail.data && <RunDrawer detail={detail.data} onClose={() => setSelectedRun(null)} />}
        </div>
        <Paper className="content-card review-rail">
          <Typography className="section-heading" variant="h6">Human review</Typography>
          <Chip size="small" color="warning" label={`${pendingReviews.length} paused`} sx={{ my: 1 }} />
          {pendingReviews.map((review) => (
            <div className="review-card" key={review.review_id}>
              <strong>{review.title}</strong>
              <p>{review.reason}</p>
              <Stack direction="row" gap={.5} flexWrap="wrap">{review.policy_evidence.map((item) => <Chip size="small" variant="outlined" key={item} label={item} />)}</Stack>
              <Typography className="subsection-heading">Requested action</Typography>
              {Object.entries(review.requested_action).map(([key, value]) => <small key={key}><b>{key.replaceAll("_", " ")}:</b> {String(value)}</small>)}
              {auth.hasRole("reviewer", "admin") && <Stack direction="row" spacing={1} mt={2}><Button size="small" color="error" onClick={() => setReviewDecision({ review, value: "reject" })}>Reject</Button><Button size="small" variant="contained" onClick={() => setReviewDecision({ review, value: "approve" })}>Approve & resume</Button></Stack>}
            </div>
          ))}
        </Paper>
      </div>
      <DecisionDialog
        open={Boolean(reviewDecision)}
        title={`${reviewDecision?.value === "approve" ? "Approve and resume" : "Reject"} workflow`}
        pending={mutation.isPending}
        onClose={() => setReviewDecision(null)}
        onSubmit={(note) => reviewDecision && mutation.mutate({ reviewId: reviewDecision.review.review_id, value: reviewDecision.value, note })}
      />
    </>
  );
}

export function SecurityPage() {
  const invocations = useQuery({ queryKey: ["mcp-invocations"], queryFn: getMcpInvocations });
  if (invocations.isPending) return <Loading />;
  if (invocations.isError) return <Alert severity="error">{invocations.error.message}</Alert>;
  return (
    <>
      <PageHeader
        eyebrow="Zero-trust tool access"
        title="MCP security boundary."
        description="Workflows never call privileged tools directly; the gateway evaluates identity, workflow, stage and human evidence."
      />
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Enforcement sequence</Typography>
          <div className="security-flow">
            {[
              ["01", "Verify identity", "Validate the Keycloak token and realm roles."],
              ["02", "Bind workflow context", "Require a registered run and declared stage for scoped tools."],
              ["03", "Evaluate tool policy", "Default deny; match the exact server, tool and role allowlist."],
              ["04", "Require human evidence", "Privileged mutations need an approved review at the same stage."],
              ["05", "Invoke and audit", "Forward through MCP and retain decision, arguments and result metadata."],
            ].map(([number, title, copy]) => <div key={number}><span>{number}</span><div><strong>{title}</strong><p>{copy}</p></div></div>)}
          </div>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Registered policy</Typography>
          <div className="policy-table">
            <div><strong>lookup_access_policy</strong><Chip size="small" color="success" label="viewer+" /><small>Discovery; no run required</small></div>
            <div><strong>validate_entitlement</strong><Chip size="small" color="warning" label="operator+" /><small>policy-evaluation stage only</small></div>
            <div><strong>submit_access_decision</strong><Chip size="small" color="error" label="reviewer+" /><small>manager-approval + approved human review</small></div>
          </div>
        </Paper>
      </div>
      <Paper className="content-card" sx={{ mt: 2 }}>
        <Typography className="section-heading" variant="h6">Gateway decision audit</Typography>
        {!invocations.data.length ? <Alert severity="info" sx={{ mt: 2 }}>No gateway calls have been attempted in this database yet.</Alert> : (
          <Table size="small">
            <TableHead><TableRow><TableCell>Decision</TableCell><TableCell>Tool</TableCell><TableCell>Identity</TableCell><TableCell>Context</TableCell><TableCell>Reason</TableCell></TableRow></TableHead>
            <TableBody>{invocations.data.map((item) => <TableRow key={item.request_id}><TableCell><Chip size="small" color={item.decision === "allowed" ? "success" : "error"} label={item.decision} /></TableCell><TableCell>{item.tool_name}</TableCell><TableCell>{item.actor_email}</TableCell><TableCell>{item.stage_id ?? "discovery"}</TableCell><TableCell>{item.reason}</TableCell></TableRow>)}</TableBody>
          </Table>
        )}
      </Paper>
    </>
  );
}
