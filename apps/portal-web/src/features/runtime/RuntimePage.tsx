import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import {
  decideHumanReview,
  getRunDetail,
  getRuntimePortfolio,
  startDummyRun,
} from "../../api";
import { useAuth } from "../../auth";
import { PageHeader } from "../../shared/components";
import type { HumanReview, WorkflowRun } from "../../types";
import { ControlLoading, DecisionDialog } from "../control/shared";
import { HumanReviewPanel } from "./HumanReviewPanel";
import { RunDetailPanel } from "./RunDetailPanel";

function RunStatus({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "success"
      : status === "failed"
        ? "error"
        : status === "waiting_for_human"
          ? "warning"
          : "info";
  return (
    <Chip
      size="small"
      color={color}
      label={status.replaceAll("_", " ")}
      sx={{ textTransform: "capitalize", fontWeight: 800 }}
    />
  );
}

export function RuntimePage() {
  const auth = useAuth();
  const queryClient = useQueryClient();
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [reviewDecision, setReviewDecision] = useState<{
    review: HumanReview;
    value: "approve" | "reject";
  } | null>(null);
  const runtime = useQuery({ queryKey: ["runtime"], queryFn: getRuntimePortfolio });
  const detail = useQuery({
    queryKey: ["run-detail", selectedRun],
    queryFn: () => getRunDetail(selectedRun!),
    enabled: Boolean(selectedRun),
  });
  const mutation = useMutation({
    mutationFn: ({
      reviewId,
      value,
      note,
    }: {
      reviewId: string;
      value: "approve" | "reject";
      note: string;
    }) => decideHumanReview(reviewId, value, note),
    onSuccess: async (result) => {
      setReviewDecision(null);
      setSelectedRun(result.run.run_id);
      await queryClient.invalidateQueries({ queryKey: ["runtime"] });
      queryClient.setQueryData(["run-detail", result.run.run_id], result);
    },
  });
  const dummyRun = useMutation({
    mutationFn: () =>
      startDummyRun({
        request_id: `DEMO-${Date.now().toString().slice(-6)}`,
        requester: "Demo Employee",
        application: "Finance Analytics",
        entitlement: "Regional Export Admin",
      }),
    onSuccess: async (result) => {
      setSelectedRun(result.run.run_id);
      await queryClient.invalidateQueries({ queryKey: ["runtime"] });
      queryClient.setQueryData(["run-detail", result.run.run_id], result);
    },
  });
  if (runtime.isPending) return <ControlLoading />;
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
              <div>
                <Typography className="section-heading" variant="h6">Workflow runs</Typography>
                <Typography variant="body2" color="text.secondary">Persistent local run state and LangGraph-ready checkpoints.</Typography>
              </div>
              <Stack direction="row" spacing={1}>
                {auth.hasRole("operator", "admin") && (
                  <Button
                    size="small"
                    variant="contained"
                    disabled={dummyRun.isPending}
                    onClick={() => dummyRun.mutate()}
                  >
                    {dummyRun.isPending ? "Starting…" : "Start dummy run"}
                  </Button>
                )}
                {Object.entries(runtime.data.status_counts).map(([status, count]) => (
                  <Chip key={status} size="small" label={`${status.replaceAll("_", " ")} ${count}`} />
                ))}
              </Stack>
            </Stack>
            <Table size="small">
              <TableHead><TableRow><TableCell>Run</TableCell><TableCell>Status</TableCell><TableCell>Current stage</TableCell><TableCell>Updated</TableCell></TableRow></TableHead>
              <TableBody>
                {runtime.data.runs.map((run: WorkflowRun) => (
                  <TableRow className="clickable-row" hover key={run.run_id} onClick={() => setSelectedRun(run.run_id)}>
                    <TableCell><strong>{run.workflow_name}</strong><br /><small>{run.run_id.slice(0, 8)} · v{run.workflow_version}</small></TableCell>
                    <TableCell><RunStatus status={run.status} /></TableCell>
                    <TableCell>{run.current_stage_id?.replaceAll("-", " ")}</TableCell>
                    <TableCell>{new Date(run.updated_at).toLocaleTimeString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
          <Alert severity="info" sx={{ mt: 2 }}>
            Dummy runs validate the governance, A2A task, MCP boundary and human-review plumbing only. The final business workflow remains intentionally undecided.
          </Alert>
          {detail.isPending && selectedRun && <ControlLoading />}
          {detail.data && <RunDetailPanel detail={detail.data} onClose={() => setSelectedRun(null)} />}
        </div>
        <HumanReviewPanel
          reviews={pendingReviews}
          onDecision={(review, value) => setReviewDecision({ review, value })}
        />
      </div>
      <DecisionDialog
        open={Boolean(reviewDecision)}
        title={`${reviewDecision?.value === "approve" ? "Approve and resume" : "Reject"} workflow`}
        pending={mutation.isPending}
        onClose={() => setReviewDecision(null)}
        onSubmit={(note) =>
          reviewDecision &&
          mutation.mutate({
            reviewId: reviewDecision.review.review_id,
            value: reviewDecision.value,
            note,
          })
        }
      />
    </>
  );
}
