#!/usr/bin/env python
"""Export a browser-based manual PDF download queue for access-controlled articles."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
DEFAULT_INPUTS = (
    OUTPUT_DIR / "latest_articles.csv",
    OUTPUT_DIR / "articles.csv",
    OUTPUT_DIR / "latest_articles.xlsx",
    OUTPUT_DIR / "articles.xlsx",
    OUTPUT_DIR / "weekly" / "weekly_latest_articles.csv",
    OUTPUT_DIR / "weekly" / "weekly_latest_articles.xlsx",
)
DEFAULT_DOWNLOAD_LOG = OUTPUT_DIR / "institutional_pdfs" / "institutional_download_log.csv"
DEFAULT_OUTPUT = OUTPUT_DIR / "manual_pdf_download_queue.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a queue of articles that need browser/manual PDF download."
    )
    parser.add_argument("--input", help="CSV/XLSX article file. Defaults to latest known output.")
    parser.add_argument("--download-log", default=str(DEFAULT_DOWNLOAD_LOG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all articles except those already marked OK in the institutional log.",
    )
    return parser.parse_args()


def find_input(path_arg: str | None) -> Path:
    if path_arg:
        path = Path(path_arg)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    for path in DEFAULT_INPUTS:
        if path.exists():
            return path
    raise FileNotFoundError("No article output file found in outputs/.")


def load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.read_excel(path, dtype=str).fillna("")


def norm_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def row_key(row: pd.Series) -> str:
    doi = norm_key(row.get("doi", ""))
    if doi:
        return f"doi:{doi}"
    title = norm_key(row.get("title", ""))
    journal = norm_key(row.get("journal", ""))
    date = norm_key(row.get("publication_date", ""))
    return f"fallback:{title}|{journal}|{date}"


def safe_filename(row: pd.Series, index: int) -> str:
    journal = str(row.get("journal", "") or "journal").strip()
    year = str(row.get("publication_date", "") or "")[:4]
    doi = str(row.get("doi", "") or "").strip().replace("/", "_")
    title = str(row.get("title", "") or "article").strip()
    base = "_".join(part for part in (journal, year, doi or title[:80]) if part)
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return (base[:160] or f"manual_article_{index}") + ".pdf"


def load_latest_log(log_path: Path) -> dict[str, dict[str, str]]:
    if not log_path.exists():
        return {}
    log_df = pd.read_csv(log_path, dtype=str).fillna("")
    latest: dict[str, dict[str, str]] = {}
    for _, row in log_df.iterrows():
        key = row_key(row)
        if key:
            latest[key] = {column: str(row.get(column, "")) for column in log_df.columns}
    return latest


def needs_manual(row: pd.Series, log_entry: dict[str, str] | None, include_all: bool) -> tuple[bool, str, str]:
    if log_entry and log_entry.get("status") == "OK":
        return False, "downloaded", ""
    if log_entry and log_entry.get("status") == "FAIL":
        return True, "needs_browser_verification", log_entry.get("message", "")
    if include_all:
        return True, "not_attempted", ""

    pdf_url = str(row.get("pdf_url", "") or "").strip()
    article_url = str(row.get("article_url", "") or "").strip()
    doi = str(row.get("doi", "") or "").strip()
    doi_url = f"https://doi.org/{doi}" if doi else ""
    if not pdf_url or pdf_url in {article_url, doi_url}:
        return True, "needs_browser_verification", "no direct PDF URL recorded"
    return False, "has_pdf_url", ""


def main() -> int:
    args = parse_args()
    input_path = find_input(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    articles = load_table(input_path)
    latest_log = load_latest_log(Path(args.download_log))
    queue_rows = []

    for index, row in articles.iterrows():
        log_entry = latest_log.get(row_key(row))
        keep, status, note = needs_manual(row, log_entry, args.include_all)
        if not keep:
            continue
        doi = str(row.get("doi", "") or "").strip()
        article_url = str(row.get("article_url", "") or "").strip()
        queue_rows.append(
            {
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
                "doi": doi,
                "publication_date": row.get("publication_date", ""),
                "article_url": article_url or (f"https://doi.org/{doi}" if doi else ""),
                "pdf_url": row.get("pdf_url", ""),
                "suggested_filename": safe_filename(row, int(index)),
                "download_status": status,
                "manual_note": note,
            }
        )

    queue = pd.DataFrame(queue_rows)
    if output_path.suffix.lower() == ".csv":
        queue.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        queue.to_excel(output_path, index=False)
        queue.to_csv(output_path.with_suffix(".csv"), index=False, encoding="utf-8-sig")

    print(f"Wrote {output_path} rows={len(queue)}")
    if output_path.suffix.lower() != ".csv":
        print(f"Wrote {output_path.with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
