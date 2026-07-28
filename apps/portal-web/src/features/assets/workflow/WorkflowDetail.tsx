import type { AssetDetail } from "../../../types";
import type { AssetDetailTab } from "../shared";
import { StructuredAssetDetail } from "../structured/StructuredAssetDetail";

export function WorkflowDetail({ detail, tab }: { detail: AssetDetail; tab: AssetDetailTab }) {
  return (
    <StructuredAssetDetail
      detail={detail}
      tab={tab}
      config={{
        notice: "This workflow is an integration dummy. Its stages and governance contract are usable, but its final business automation is intentionally not decided.",
        overview: ["implementation_status", "orchestrator", "entrypoint"],
        structure: ["stages", "dependencies", "a2a", "checkpointing"],
        governance: ["failure_policy"],
      }}
    />
  );
}
