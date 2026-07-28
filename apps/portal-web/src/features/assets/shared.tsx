import { Alert, Paper, Typography } from "@mui/material";

import type { AssetDetail } from "../../types";

export type AssetDetailTab = "overview" | "structure" | "governance" | "activity";

export function MetadataValue({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  return (
    <div className="label-value">
      <span>{label}</span>
      <strong>{String(value ?? "Not recorded").replaceAll("_", " ")}</strong>
    </div>
  );
}

export function AssetTimeline({ detail }: { detail: AssetDetail }) {
  if (!detail.audit_events.length) {
    return (
      <Alert severity="info">
        No audit events have been recorded for this version.
      </Alert>
    );
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
