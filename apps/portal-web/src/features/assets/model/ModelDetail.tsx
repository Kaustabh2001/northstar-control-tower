import type { AssetDetail } from "../../../types";
import type { AssetDetailTab } from "../shared";
import { StructuredAssetDetail } from "../structured/StructuredAssetDetail";

export function ModelDetail({ detail, tab }: { detail: AssetDetail; tab: AssetDetailTab }) {
  return (
    <StructuredAssetDetail
      detail={detail}
      tab={tab}
      config={{
        overview: ["model_family", "task", "artifact"],
        structure: ["training_dataset", "deployment"],
        governance: ["metrics", "operating_thresholds", "controls"],
      }}
    />
  );
}
