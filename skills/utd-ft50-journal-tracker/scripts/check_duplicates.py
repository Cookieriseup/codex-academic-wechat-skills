#!/usr/bin/env python
"""Check latest article outputs for duplicate DOI or suspected duplicate titles."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
REPORT_PATH = ROOT / "duplicate_report.md"


def load_latest_articles() -> tuple[pd.DataFrame, Path]:
    csv_path = OUTPUT_DIR / "latest_articles.csv"
    xlsx_path = OUTPUT_DIR / "latest_articles.xlsx"
    fallback_csv = OUTPUT_DIR / "articles.csv"
    fallback_xlsx = OUTPUT_DIR / "articles.xlsx"
    smoke_xlsx = OUTPUT_DIR / "smoke_test_latest_articles.xlsx"

    if csv_path.exists():
        return pd.read_csv(csv_path, dtype=str).fillna(""), csv_path
    if xlsx_path.exists():
        return pd.read_excel(xlsx_path, dtype=str).fillna(""), xlsx_path
    if fallback_csv.exists():
        return pd.read_csv(fallback_csv, dtype=str).fillna(""), fallback_csv
    if fallback_xlsx.exists():
        return pd.read_excel(fallback_xlsx, dtype=str).fillna(""), fallback_xlsx
    if smoke_xlsx.exists():
        return pd.read_excel(smoke_xlsx, sheet_name="latest_articles", dtype=str).fillna(""), smoke_xlsx
    return pd.DataFrame(), csv_path


def normalize_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df:
        return pd.Series([""] * len(df), index=df.index)
    return df[column].fillna("").astype(str).str.strip().str.lower()


def duplicate_rows(df: pd.DataFrame, key: pd.Series) -> pd.DataFrame:
    mask = key.ne("") & key.duplicated(keep=False)
    return df.loc[mask].copy()


def main() -> int:
    df, source_path = load_latest_articles()
    lines = ["# Duplicate Report", "", f"- Source file: {source_path}", f"- Total rows: {len(df)}"]

    if df.empty:
        lines.extend(["", "No article output file was found or the file is empty."])
        REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {REPORT_PATH}")
        return 1

    doi_duplicates = duplicate_rows(df, normalize_series(df, "doi"))
    suspected_key = (
        normalize_series(df, "title")
        + "|"
        + normalize_series(df, "journal")
        + "|"
        + normalize_series(df, "publication_date")
    )
    missing_doi = normalize_series(df, "doi").eq("")
    suspected_duplicates = df.loc[missing_doi & suspected_key.duplicated(keep=False)].copy()

    lines.extend(
        [
            f"- Duplicate DOI rows: {len(doi_duplicates)}",
            f"- Suspected duplicate rows without DOI: {len(suspected_duplicates)}",
            "",
            "## Duplicate DOI Rows",
            "",
        ]
    )
    if doi_duplicates.empty:
        lines.append("None")
    else:
        lines.extend(["| doi | journal | title | publication_date |", "| --- | --- | --- | --- |"])
        for _, row in doi_duplicates.iterrows():
            lines.append(
                f"| {row.get('doi', '')} | {row.get('journal', '')} | {row.get('title', '')} | {row.get('publication_date', '')} |"
            )

    lines.extend(["", "## Suspected Duplicates Without DOI", ""])
    if suspected_duplicates.empty:
        lines.append("None")
    else:
        lines.extend(["| journal | title | publication_date |", "| --- | --- | --- |"])
        for _, row in suspected_duplicates.iterrows():
            lines.append(f"| {row.get('journal', '')} | {row.get('title', '')} | {row.get('publication_date', '')} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0 if doi_duplicates.empty and suspected_duplicates.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
