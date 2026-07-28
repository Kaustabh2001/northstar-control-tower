import { Alert, Paper, Typography } from "@mui/material";

import type { AssetDetail } from "../../../types";
import {
  type AssetDetailTab,
  AssetTimeline,
  MetadataValue,
} from "../shared";

export function GenericAssetDetail({
  detail,
  tab,
}: {
  detail: AssetDetail;
  tab: AssetDetailTab;
}) {
  if (tab === "activity") return <AssetTimeline detail={detail} />;
  return (
    <Paper className="content-card">
      <Alert severity="info" sx={{ mb: 2 }}>
        This asset is governed through the shared registry contract. A
        type-specific operational module will be added with its real source.
      </Alert>
      <Typography className="section-heading" variant="h6">Registry contract</Typography>
      <Typography className="body-emphasis">{detail.asset.intended_use}</Typography>
      <div className="metric-detail-grid">
        <MetadataValue label="Owner" value={detail.asset.owner} />
        <MetadataValue label="Asset type" value={detail.asset.asset_type} />
        <MetadataValue label="Risk" value={detail.asset.risk_level} />
        <MetadataValue label="Source commit" value={detail.asset.source_commit} />
        <MetadataValue label="Created" value={new Date(detail.asset.created_at).toLocaleString()} />
        <MetadataValue label="Updated" value={new Date(detail.asset.updated_at).toLocaleString()} />
      </div>
    </Paper>
  );
}
