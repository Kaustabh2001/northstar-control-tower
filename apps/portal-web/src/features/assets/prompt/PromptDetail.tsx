import type { AssetDetail } from "../../../types";
import type { AssetDetailTab } from "../shared";
import { StructuredAssetDetail } from "../structured/StructuredAssetDetail";

export function PromptDetail({ detail, tab }: { detail: AssetDetail; tab: AssetDetailTab }) {
  return (
    <StructuredAssetDetail
      detail={detail}
      tab={tab}
      config={{
        overview: ["template", "change_summary"],
        structure: ["variables", "model_compatibility"],
        governance: ["evaluation", "guardrails"],
      }}
    />
  );
}
