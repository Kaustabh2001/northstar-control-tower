import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Chip,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";

import { getAssetDetail } from "./api";
import { DatasetDetail } from "./features/assets/dataset/DatasetDetail";
import { GenericAssetDetail } from "./features/assets/generic/GenericAssetDetail";
import { McpServerDetail } from "./features/assets/mcp/McpServerDetail";
import type { AssetDetailTab } from "./features/assets/shared";
import { LoadingPanel, StatusChip } from "./shared/components";
import type { Asset } from "./types";

export function AssetDetailPage({
  assetId,
  version,
  onBack,
}: {
  assetId: string;
  version: string;
  onBack: (type: Asset["asset_type"]) => void;
}) {
  const [tab, setTab] = useState<AssetDetailTab>("overview");
  const [refreshLive, setRefreshLive] = useState(false);
  const detail = useQuery({
    queryKey: ["asset-detail", assetId, version, refreshLive],
    queryFn: () => getAssetDetail(assetId, version, refreshLive),
  });
  if (detail.isPending) return <LoadingPanel label="Loading asset evidence…" />;
  if (detail.isError) return <Alert severity="error">{detail.error.message}</Alert>;
  const data = detail.data;
  return (
    <>
      <button className="back-link" onClick={() => onBack(data.asset.asset_type)}>← Back to inventory</button>
      <section className="agent-hero">
        <div className="agent-avatar">{data.asset.asset_type === "dataset" ? "DS" : data.asset.asset_type === "mcp_server" ? "MC" : "AI"}</div>
        <div className="agent-title">
          <span>{data.detail_kind.replaceAll("_", " ")} · {data.asset.asset_id}</span>
          <Typography className="strong-heading" variant="h3">{data.asset.display_name}</Typography>
          <Typography color="text.secondary">{data.asset.intended_use}</Typography>
          <Stack direction="row" spacing={1} mt={1.5}>
            <StatusChip asset={data.asset} />
            <Chip size="small" variant="outlined" label={`Risk: ${data.asset.risk_level}`} />
            <Chip size="small" variant="outlined" label={`v${data.asset.version}`} />
          </Stack>
        </div>
      </section>
      <Paper className="detail-tabs">
        <Tabs value={tab} onChange={(_, value: AssetDetailTab) => setTab(value)} variant="scrollable">
          <Tab value="overview" label="Overview" />
          <Tab value="structure" label={data.asset.asset_type === "dataset" ? "Schema & privacy" : data.asset.asset_type === "mcp_server" ? "Tools & schemas" : "Structure"} />
          <Tab value="governance" label={data.asset.asset_type === "dataset" ? "Quality & controls" : "Governance"} />
          <Tab value="activity" label="Versions & audit" />
        </Tabs>
      </Paper>
      <div className="tab-content">
        {data.asset.asset_type === "dataset" ? (
          <DatasetDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "mcp_server" ? (
          <McpServerDetail detail={data} tab={tab} onRefresh={() => setRefreshLive(true)} refreshing={detail.isFetching} />
        ) : (
          <GenericAssetDetail detail={data} tab={tab} />
        )}
      </div>
    </>
  );
}
