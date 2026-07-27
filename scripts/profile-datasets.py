import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CC0_PATH = (
    ROOT
    / "data"
    / "raw"
    / "it-service-ticket-classification"
    / "all_tickets_processed_improved_v3.csv"
)
RICH_PATH = ROOT / "data" / "raw" / "customer-support-tickets-multilingual.csv"
IT_QUEUES = {
    "Technical Support",
    "Product Support",
    "IT Support",
    "Service Outages and Maintenance",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_duplicates(series: pd.Series) -> int:
    normalized = (
        series.fillna("")
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return int(normalized.duplicated().sum())


cc0 = pd.read_csv(CC0_PATH)
rich = pd.read_csv(RICH_PATH)
english = rich[rich["language"].eq("en")].copy()
english_it = english[english["queue"].isin(IT_QUEUES)].copy()

profile = {
    "sources": {
        CC0_PATH.name: {"sha256": sha256(CC0_PATH), "rows": len(cc0)},
        RICH_PATH.name: {"sha256": sha256(RICH_PATH), "rows": len(rich)},
    },
    "cc0": {
        "columns": cc0.columns.tolist(),
        "missing": cc0.isna().sum().to_dict(),
        "full_row_duplicates": int(cc0.duplicated().sum()),
        "normalized_text_duplicates": normalized_duplicates(cc0["Document"]),
        "average_words": round(cc0["Document"].str.split().str.len().mean(), 1),
        "labels": cc0["Topic_group"].value_counts().to_dict(),
    },
    "rich_english": {
        "rows": len(english),
        "missing": english.isna().sum().to_dict(),
        "full_row_duplicates": int(english.duplicated().sum()),
        "normalized_body_duplicates": normalized_duplicates(english["body"]),
        "normalized_answer_duplicates": normalized_duplicates(english["answer"]),
        "average_body_words": round(english["body"].str.split().str.len().mean(), 1),
        "average_answer_words": round(
            english["answer"].fillna("").str.split().str.len().mean(), 1
        ),
    },
    "english_it_subset": {
        "rows": len(english_it),
        "queues": english_it["queue"].value_counts().to_dict(),
        "types": english_it["type"].value_counts().to_dict(),
        "priorities": english_it["priority"].value_counts().to_dict(),
    },
}

print(json.dumps(profile, ensure_ascii=False, indent=2))
