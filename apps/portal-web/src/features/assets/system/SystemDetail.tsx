import type { AssetDetail } from "../../../types";
import type { AssetDetailTab } from "../shared";
import { StructuredAssetDetail } from "../structured/StructuredAssetDetail";

export function SystemDetail({ detail, tab }: { detail: AssetDetail; tab: AssetDetailTab }) {
  return (
    <StructuredAssetDetail
      detail={detail}
      tab={tab}
      config={{
        overview: ["business_process", "service_tier", "components"],
        structure: ["deployment", "components"],
        governance: ["risk_profile", "controls"],
      }}
    />
  );
}
