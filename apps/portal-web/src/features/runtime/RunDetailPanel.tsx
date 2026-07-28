import {
  Alert,
  Button,
  Divider,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import type { RunDetail } from "../../types";

export function RunDetailPanel({
  detail,
  onClose,
}: {
  detail: RunDetail;
  onClose: () => void;
}) {
  return (
    <Paper className="run-detail-panel">
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
        <div>
          <Typography className="section-heading" variant="h6">
            Run {detail.run.run_id.slice(0, 8)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {detail.run.correlation.trace_id}
          </Typography>
        </div>
        <Button size="small" onClick={onClose}>Close</Button>
      </Stack>
      <div className="stage-track">
        {detail.run.stages.map((stage, index) => (
          <div className={`stage-step stage-${stage.status}`} key={stage.stage_id}>
            <span>{index + 1}</span>
            <div>
              <strong>{stage.display_name}</strong>
              <small>{stage.status.replaceAll("_", " ")} · {stage.kind}</small>
            </div>
          </div>
        ))}
      </div>
      {detail.run.error_summary && (
        <Alert severity="error">
          {detail.run.error_code}: {detail.run.error_summary}
        </Alert>
      )}
      <Divider sx={{ my: 2 }} />
      <Typography className="subsection-heading">Trace events</Typography>
      <div className="timeline">
        {detail.events.map((event) => (
          <div className="timeline-item" key={event.event_id}>
            <i />
            <div>
              <strong>{event.event_type.replaceAll(".", " ")}</strong>
              <p>{event.stage_id ?? "workflow"}</p>
              <small>{event.actor_id} · {new Date(event.occurred_at).toLocaleString()}</small>
            </div>
          </div>
        ))}
      </div>
    </Paper>
  );
}
