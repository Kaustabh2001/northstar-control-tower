import { Alert, Chip, Paper, Typography } from "@mui/material";

import type { AssetDetail } from "../../../types";
import {
  type AssetDetailTab,
  AssetTimeline,
  MetadataValue,
} from "../shared";

interface StructuredAssetConfig {
  overview: string[];
  structure: string[];
  governance: string[];
  notice?: string;
}

function HumanValue({ value }: { value: unknown }) {
  if (Array.isArray(value)) {
    return (
      <div className="evidence-list">
        {value.map((item, index) => (
          <div key={`${index}-${JSON.stringify(item)}`}>
            {typeof item === "object" && item !== null ? (
              Object.entries(item).map(([key, nested]) => (
                <MetadataValue key={key} label={key} value={nested} />
              ))
            ) : (
              <Chip size="small" label={String(item)} />
            )}
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === "object" && value !== null) {
    return (
      <div className="metric-detail-grid">
        {Object.entries(value).map(([key, nested]) => (
          <MetadataValue
            key={key}
            label={key}
            value={
              typeof nested === "object" ? JSON.stringify(nested) : nested
            }
          />
        ))}
      </div>
    );
  }
  return <Typography className="body-emphasis">{String(value ?? "Not recorded")}</Typography>;
}

export function StructuredAssetDetail({
  detail,
  tab,
  config,
}: {
  detail: AssetDetail;
  tab: AssetDetailTab;
  config: StructuredAssetConfig;
}) {
  if (tab === "activity") return <AssetTimeline detail={detail} />;
  const keys =
    tab === "structure"
      ? config.structure
      : tab === "governance"
        ? config.governance
        : config.overview;
  return (
    <>
      {config.notice && tab === "overview" && (
        <Alert severity="warning" sx={{ mb: 2 }}>{config.notice}</Alert>
      )}
      <div className="detail-grid">
        {keys.map((key) => (
          <Paper className="content-card" key={key}>
            <Typography className="section-heading" variant="h6">
              {key.replaceAll("_", " ")}
            </Typography>
            <HumanValue value={detail.metadata[key]} />
          </Paper>
        ))}
      </div>
    </>
  );
}
