import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";

import { getAssetDetail, performEmergencyAction } from "./api";
import { useAuth } from "./auth";
import { DecisionDialog } from "./features/control/shared";
import { DatasetDetail } from "./features/assets/dataset/DatasetDetail";
import { GenericAssetDetail } from "./features/assets/generic/GenericAssetDetail";
import { McpServerDetail } from "./features/assets/mcp/McpServerDetail";
import { KnowledgeIndexDetail } from "./features/assets/knowledge-index/KnowledgeIndexDetail";
import { ModelDetail } from "./features/assets/model/ModelDetail";
import { PromptDetail } from "./features/assets/prompt/PromptDetail";
import { SystemDetail } from "./features/assets/system/SystemDetail";
import { WorkflowDetail } from "./features/assets/workflow/WorkflowDetail";
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
  const [emergencyAction, setEmergencyAction] = useState<"suspend" | "rollback" | null>(null);
  const auth = useAuth();
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ["asset-detail", assetId, version, refreshLive],
    queryFn: () => getAssetDetail(assetId, version, refreshLive),
  });
  const emergency = useMutation({
    mutationFn: (reason: string) => {
      const previousVersion = detail.data?.version_history.find(
        (item) => item.version !== version,
      )?.version;
      return performEmergencyAction(
        assetId,
        version,
        emergencyAction!,
        reason,
        previousVersion,
      );
    },
    onSuccess: async () => {
      setEmergencyAction(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["asset-detail", assetId, version] }),
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
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
            {auth.hasRole("admin") && !["suspended", "retired"].includes(data.asset.governance_state) && (
              <Button size="small" color="error" onClick={() => setEmergencyAction("suspend")}>
                Suspend
              </Button>
            )}
            {auth.hasRole("admin") && data.version_history.some((item) => item.version !== version) && (
              <Button size="small" variant="outlined" onClick={() => setEmergencyAction("rollback")}>
                Roll back
              </Button>
            )}
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
        ) : data.asset.asset_type === "ai_system" ? (
          <SystemDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "agentic_workflow" ? (
          <WorkflowDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "model" ? (
          <ModelDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "prompt" ? (
          <PromptDetail detail={data} tab={tab} />
        ) : data.asset.asset_type === "knowledge_index" ? (
          <KnowledgeIndexDetail detail={data} tab={tab} />
        ) : (
          <GenericAssetDetail detail={data} tab={tab} />
        )}
      </div>
      <DecisionDialog
        open={Boolean(emergencyAction)}
        title={emergencyAction === "rollback" ? "Roll back this asset" : "Suspend this asset"}
        pending={emergency.isPending}
        onClose={() => setEmergencyAction(null)}
        onSubmit={(reason) => emergency.mutate(reason)}
      />
    </>
  );
}
