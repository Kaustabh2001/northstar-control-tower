import type { AssetDetail } from "../../../types";
import type { AssetDetailTab } from "../shared";
import { StructuredAssetDetail } from "../structured/StructuredAssetDetail";

export function KnowledgeIndexDetail({ detail, tab }: { detail: AssetDetail; tab: AssetDetailTab }) {
  return (
    <StructuredAssetDetail
      detail={detail}
      tab={tab}
      config={{
        overview: ["engine", "index_name", "documents", "chunks"],
        structure: ["embedding_model", "chunking", "retrieval"],
        governance: ["freshness", "access_policy"],
      }}
    />
  );
}
