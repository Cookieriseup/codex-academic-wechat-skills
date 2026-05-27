#!/usr/bin/env python
"""Create per-journal field completeness report for latest article outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
REPORT_PATH = OUTPUT_DIR / "field_completeness_report.xlsx"
FIELDS = ["title", "authors", "abstract", "doi", "publication_date", "article_url", "pdf_url", "affiliations"]


def load_articles() -> tuple[pd.DataFrame, Path]:
    for path in (
        OUTPUT_DIR / "latest_articles.csv",
        OUTPUT_DIR / "latest_articles.xlsx",
        OUTPUT_DIR / "articles.csv",
        OUTPUT_DIR / "articles.xlsx",
        OUTPUT_DIR / "smoke_test_latest_articles.xlsx",
    ):
        if path.exists() and path.suffix == ".csv":
            return pd.read_csv(path, dtype=str).fillna(""), path
        if path.exists() and path.suffix == ".xlsx":
            sheet_name = "latest_articles" if path.name == "smoke_test_latest_articles.xlsx" else 0
            return pd.read_excel(path, sheet_name=sheet_name, dtype=str).fillna(""), path
    return pd.DataFrame(), OUTPUT_DIR / "latest_articles.csv"


def completeness_for_group(journal: str, group: pd.DataFrame) -> dict[str, object]:
    row: dict[str, object] = {"journal": journal, "record_count": len(group)}
    for field in FIELDS:
        if field not in group:
            row[f"{field}_completeness"] = 0
        else:
            row[f"{field}_completeness"] = group[field].fillna("").astype(str).str.strip().ne("").mean()
    return row


def main() -> int:
    df, source_path = load_articles()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if df.empty or "journal" not in df:
        report = pd.DataFrame(columns=["journal", "record_count"] + [f"{field}_completeness" for field in FIELDS])
    else:
        report = pd.DataFrame(
            completeness_for_group(journal, group)
            for journal, group in df.groupby("journal", dropna=False)
        ).sort_values("journal")

    summary = pd.DataFrame(
        [{"source_file": str(source_path), "total_rows": len(df), "generated_report": str(REPORT_PATH)}]
    )
    with pd.ExcelWriter(REPORT_PATH) as writer:
        report.to_excel(writer, sheet_name="by_journal", index=False)
        summary.to_excel(writer, sheet_name="summary", index=False)

    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
