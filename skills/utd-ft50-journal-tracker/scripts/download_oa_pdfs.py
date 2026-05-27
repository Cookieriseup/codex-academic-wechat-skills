#!/usr/bin/env python
"""Download legal open-access PDFs from tracked article outputs.

This script downloads only URLs already recorded in the `pdf_url` column, which
should come from OpenAlex or Unpaywall OA metadata. It does not attempt to bypass
publisher paywalls or institutional access controls.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
DEFAULT_INPUTS = (
    OUTPUT_DIR / "latest_articles.csv",
    OUTPUT_DIR / "articles.csv",
    OUTPUT_DIR / "latest_articles.xlsx",
    OUTPUT_DIR / "articles.xlsx",
    OUTPUT_DIR / "smoke_test_latest_articles.xlsx",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download OA PDFs listed in article outputs.")
    parser.add_argument("--input", help="CSV/XLSX file containing a pdf_url column. Defaults to the newest known output.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR / "pdfs"), help="Directory for downloaded PDF files.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of PDFs to download; 0 means no limit.")
    parser.add_argument("--overwrite", action="store_true", help="Re-download files that already exist.")
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


def load_articles(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str).fillna("")
    sheet_name = "latest_articles" if path.name == "smoke_test_latest_articles.xlsx" else 0
    return pd.read_excel(path, sheet_name=sheet_name, dtype=str).fillna("")


def safe_filename(row: pd.Series, index: int) -> str:
    doi = str(row.get("doi", "")).strip().replace("/", "_")
    title = str(row.get("title", "article")).strip()
    year = str(row.get("publication_date", ""))[:4]
    base = doi or f"{year}_{title[:80]}" or f"article_{index}"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return (base[:150] or f"article_{index}") + ".pdf"


def looks_like_pdf(response: requests.Response) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    return "pdf" in content_type or response.content[:4] == b"%PDF"


def download_pdf(session: requests.Session, url: str, path: Path) -> tuple[bool, str]:
    try:
        response = session.get(url, timeout=60, allow_redirects=True)
        response.raise_for_status()
        if not looks_like_pdf(response):
            return False, f"URL did not return a PDF: {response.headers.get('content-type', '')}"
        path.write_bytes(response.content)
        return True, "downloaded"
    except requests.RequestException as exc:
        return False, str(exc)


def main() -> int:
    args = parse_args()
    input_path = find_input(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_articles(input_path)

    if "pdf_url" not in df:
        raise ValueError(f"{input_path} does not contain a pdf_url column")

    session = requests.Session()
    session.headers.update({"User-Agent": "utd-ft-journal-tracker/0.1 OA PDF downloader"})
    rows = df[df["pdf_url"].astype(str).str.strip().ne("")]
    if args.limit > 0:
        rows = rows.head(args.limit)

    log_rows = []
    for idx, row in rows.iterrows():
        url = str(row.get("pdf_url", "")).strip()
        filename = safe_filename(row, int(idx))
        path = output_dir / filename
        if path.exists() and not args.overwrite:
            ok, message = True, "already exists"
        else:
            ok, message = download_pdf(session, url, path)
        log_rows.append(
            {
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "pdf_url": url,
                "file": str(path if ok else ""),
                "status": "OK" if ok else "FAIL",
                "message": message,
            }
        )
        print(f"{log_rows[-1]['status']}: {row.get('title', '')[:80]} - {message}")

    log_path = output_dir / "download_log.csv"
    pd.DataFrame(log_rows).to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"Wrote {log_path}")
    return 0 if not log_rows or all(row["status"] == "OK" for row in log_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
