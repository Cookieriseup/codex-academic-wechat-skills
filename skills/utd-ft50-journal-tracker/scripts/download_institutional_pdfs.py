#!/usr/bin/env python
"""Download PDFs through institutional access without using Python proxy env vars."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

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
URL_COLUMNS = ("publisher_pdf_url", "doi_url", "article_url")
HTML_LOGIN_PATTERNS = (
    "login",
    "sign in",
    "institutional login",
    "shibboleth",
    "saml",
    "captcha",
    "access denied",
    "forbidden",
    "unauthorized",
    "权限",
    "登录",
    "验证码",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download institutionally accessible PDFs.")
    parser.add_argument("--input", help="CSV/XLSX article file. Defaults to the newest known output.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR / "institutional_pdfs"))
    parser.add_argument("--access-mode", choices=["campus_ip"], default="campus_ip")
    parser.add_argument("--limit", type=int, default=0, help="Maximum rows to attempt; 0 means no limit.")
    parser.add_argument("--overwrite", action="store_true", help="Re-download existing files.")
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


def build_doi_url(doi: str) -> str:
    doi = str(doi or "").strip()
    return f"https://doi.org/{doi}" if doi else ""


def candidate_urls(row: pd.Series) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for column in URL_COLUMNS:
        if column == "doi_url":
            url = str(row.get("doi_url", "") or "").strip() or build_doi_url(row.get("doi", ""))
        else:
            url = str(row.get(column, "") or "").strip()
        if url:
            values.append((column, url))
    return values


def safe_filename(row: pd.Series, index: int) -> str:
    doi = str(row.get("doi", "")).strip().replace("/", "_")
    title = str(row.get("title", "article")).strip()
    year = str(row.get("publication_date", ""))[:4]
    base = doi or f"{year}_{title[:80]}" or f"article_{index}"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return (base[:150] or f"article_{index}") + ".pdf"


def make_campus_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 institutional-pdf-checker/0.1 "
                "(campus_ip mode; no proxy env)"
            )
        }
    )
    return session


def is_pdf_response(response: requests.Response, sample: bytes) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    return "pdf" in content_type or sample.startswith(b"%PDF")


def html_failure_reason(response: requests.Response, sample: bytes) -> str:
    content_type = response.headers.get("content-type", "").lower()
    text = sample[:8192].decode(response.encoding or "utf-8", errors="ignore").lower()
    if response.status_code in (401, 403):
        return f"HTTP {response.status_code}: unauthorized/forbidden"
    if any(pattern in text for pattern in HTML_LOGIN_PATTERNS):
        return f"HTML/login/captcha/access page: {content_type}"
    if "html" in content_type or sample.lstrip().startswith(b"<!DOCTYPE") or sample.lstrip().startswith(b"<html"):
        return f"HTML page, not PDF: {content_type}"
    return f"not PDF: HTTP {response.status_code}, {content_type or 'unknown content-type'}"


def attempt_download(session: requests.Session, url: str, output_path: Path) -> tuple[bool, str, str, int | str, str]:
    try:
        with session.get(url, timeout=90, allow_redirects=True, stream=True) as response:
            final_url = response.url
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")
            sample = next(response.iter_content(chunk_size=8192), b"")
            if not response.ok:
                return False, html_failure_reason(response, sample), final_url, status_code, content_type
            if not is_pdf_response(response, sample):
                return False, html_failure_reason(response, sample), final_url, status_code, content_type

            with output_path.open("wb") as handle:
                handle.write(sample)
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        handle.write(chunk)
            return True, "downloaded PDF via campus_ip direct session", final_url, status_code, content_type
    except requests.RequestException as exc:
        return False, f"request failed: {exc}", url, "", ""


def main() -> int:
    args = parse_args()
    input_path = find_input(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_articles(input_path)
    session = make_campus_session()

    rows = df.copy()
    if args.limit > 0:
        rows = rows.head(args.limit)

    log_rows = []
    for idx, row in rows.iterrows():
        filename = safe_filename(row, int(idx))
        output_path = output_dir / filename
        if output_path.exists() and not args.overwrite:
            log_rows.append(
                {
                    "journal": row.get("journal", ""),
                    "title": row.get("title", ""),
                    "doi": row.get("doi", ""),
                    "url_source": "",
                    "attempted_url": "",
                    "final_url": "",
                    "http_status": "",
                    "content_type": "",
                    "file": str(output_path),
                    "status": "OK",
                    "message": "already exists",
                }
            )
            continue

        candidates = candidate_urls(row)
        if not candidates:
            log_rows.append(
                {
                    "journal": row.get("journal", ""),
                    "title": row.get("title", ""),
                    "doi": row.get("doi", ""),
                    "url_source": "",
                    "attempted_url": "",
                    "final_url": "",
                    "http_status": "",
                    "content_type": "",
                    "file": "",
                    "status": "FAIL",
                    "message": "no publisher_pdf_url, doi_url, article_url, or doi available",
                }
            )
            continue

        ok = False
        last_log = {}
        for source, url in candidates:
            ok, message, final_url, status_code, content_type = attempt_download(session, url, output_path)
            last_log = {
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "url_source": source,
                "attempted_url": url,
                "final_url": final_url,
                "http_status": status_code,
                "content_type": content_type,
                "file": str(output_path if ok else ""),
                "status": "OK" if ok else "FAIL",
                "message": message,
            }
            if ok:
                break

        log_rows.append(last_log)
        print(f"{last_log['status']}: {row.get('title', '')[:80]} - {last_log['message']}")

    log_path = output_dir / "institutional_download_log.csv"
    pd.DataFrame(log_rows).to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"Wrote {log_path}")
    return 0 if all(row["status"] == "OK" for row in log_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
