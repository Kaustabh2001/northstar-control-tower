import type { ReactNode } from "react";
import { Chip, CircularProgress, Paper, Typography } from "@mui/material";

import type { Asset } from "../types";

export function PageHeader({
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

export function StatusChip({ asset }: { asset: Asset }) {
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

export function LoadingPanel({
  label = "Loading control-plane data…",
}: {
  label?: string;
}) {
  return (
    <Paper className="loading-panel">
      <CircularProgress size={24} />
      <Typography color="text.secondary">{label}</Typography>
    </Paper>
  );
}

export function LabelValue({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="label-value">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
