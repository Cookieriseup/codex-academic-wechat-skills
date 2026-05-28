#!/usr/bin/env python
"""Match browser-downloaded PDFs back to the manual download queue."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
DEFAULT_QUEUE = OUTPUT_DIR / "manual_pdf_download_queue.xlsx"
DEFAULT_SOURCE_DIR = Path.home() / "Downloads"
DEFAULT_OUTPUT_DIR = OUTPUT_DIR / "manual_pdfs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile manually downloaded PDFs with the article queue.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    parser.add_argument("--pdf-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--copy", action="store_true", help="Copy matched PDFs into output-dir/matched.")
    return parser.parse_args()


def load_queue(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.read_excel(path, dtype=str).fillna("")


def normalize(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def doi_tokens(doi: str) -> list[str]:
    doi = str(doi or "").strip().lower()
    if not doi:
        return []
    return [normalize(doi), normalize(doi.replace("/", "_")), normalize(doi.split("/")[-1])]


def title_token(title: str) -> str:
    return normalize(str(title or ""))[:60]


def match_pdf(row: pd.Series, pdfs: list[Path]) -> Path | None:
    filename = normalize(row.get("suggested_filename", ""))
    doi_parts = [token for token in doi_tokens(str(row.get("doi", ""))) if len(token) >= 8]
    title_part = title_token(str(row.get("title", "")))

    for pdf in pdfs:
        stem = normalize(pdf.stem)
        if filename and filename.replace("pdf", "") in stem:
            return pdf
        if any(token in stem for token in doi_parts):
            return pdf
        if len(title_part) >= 30 and title_part in stem:
            return pdf
    return None


def main() -> int:
    args = parse_args()
    queue_path = Path(args.queue)
    pdf_dir = Path(args.pdf_dir)
    output_dir = Path(args.output_dir)
    matched_dir = output_dir / "matched"
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.copy:
        matched_dir.mkdir(parents=True, exist_ok=True)

    queue = load_queue(queue_path)
    pdfs = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    rows = []

    for _, row in queue.iterrows():
        matched = match_pdf(row, pdfs)
        copied_to = ""
        status = "matched" if matched else "missing"
        if matched and args.copy:
            target_name = str(row.get("suggested_filename", "") or matched.name)
            target = matched_dir / target_name
            shutil.copy2(matched, target)
            copied_to = str(target)
        rows.append(
            {
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "suggested_filename": row.get("suggested_filename", ""),
                "status": status,
                "matched_pdf": str(matched or ""),
                "copied_to": copied_to,
            }
        )

    log_path = output_dir / "manual_pdf_reconcile_log.csv"
    pd.DataFrame(rows).to_csv(log_path, index=False, encoding="utf-8-sig")
    matched_count = sum(row["status"] == "matched" for row in rows)
    print(f"Wrote {log_path}")
    print(f"Matched {matched_count} of {len(rows)} queue rows from {pdf_dir}")
    if not args.copy:
        print("Dry run only. Add --copy to copy matched PDFs into the project.")
    return 0 if matched_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
