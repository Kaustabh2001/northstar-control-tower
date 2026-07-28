import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Chip, Paper, Stack, Typography } from "@mui/material";

import { decideApproval, getGovernancePortfolio } from "../../api";
import { useAuth } from "../../auth";
import { PageHeader } from "../../shared/components";
import type { GovernanceApproval } from "../../types";
import { ControlLoading, DecisionDialog } from "../control/shared";

export function GovernancePage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [decision, setDecision] = useState<{
    approval: GovernanceApproval;
    value: "approve" | "reject";
  } | null>(null);
  const portfolio = useQuery({
    queryKey: ["governance"],
    queryFn: getGovernancePortfolio,
  });
  const mutation = useMutation({
    mutationFn: ({
      approvalId,
      value,
      note,
    }: {
      approvalId: string;
      value: "approve" | "reject";
      note: string;
    }) => decideApproval(approvalId, value, note),
    onSuccess: async () => {
      setDecision(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["governance"] }),
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });
  if (portfolio.isPending) return <ControlLoading />;
  if (portfolio.isError) {
    return <Alert severity="error">{portfolio.error.message}</Alert>;
  }
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
          <Typography variant="body2" color="text.secondary">
            Decisions advance the registered version only after its evidence gate is satisfied.
          </Typography>
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
        onSubmit={(note) =>
          decision &&
          mutation.mutate({
            approvalId: decision.approval.approval_id,
            value: decision.value,
            note,
          })
        }
      />
    </>
  );
}
