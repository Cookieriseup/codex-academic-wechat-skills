#!/usr/bin/env python
"""Fetch recent UTD24/FT50 journal articles and export CSV, Excel, and BibTeX."""

from __future__ import annotations

import argparse
import html
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
JOURNALS_PATH = ROOT / "journals.yaml"
OUTPUT_DIR = ROOT / "outputs"
CSV_PATH = OUTPUT_DIR / "articles.csv"
XLSX_PATH = OUTPUT_DIR / "articles.xlsx"
BIB_PATH = OUTPUT_DIR / "articles.bib"

EXCEL_COLUMNS = [
    "journal",
    "list_type",
    "title",
    "authors",
    "affiliations",
    "abstract",
    "doi",
    "publication_date",
    "volume",
    "issue",
    "pages",
    "article_url",
    "is_oa",
    "pdf_url",
    "source_api",
    "fetched_at",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track latest UTD24 and FT50 journal articles.")
    parser.add_argument("--from-date", required=True, help="Start publication date, YYYY-MM-DD.")
    parser.add_argument("--to-date", required=True, help="End publication date, YYYY-MM-DD.")
    parser.add_argument("--journals", default=str(JOURNALS_PATH), help="Path to journals.yaml.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Directory for output files.")
    parser.add_argument(
        "--list",
        choices=["union", "UTD24", "FT50", "both", "all-configured"],
        default="union",
        help=(
            "Journal subset to fetch. Default 'union' tracks journals marked UTD24 or FT50. "
            "Use 'all-configured' only when you intentionally want optional watchlist journals too."
        ),
    )
    parser.add_argument("--rows", type=int, default=100, help="Crossref page size per request.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API calls in seconds.")
    return parser.parse_args()


def parse_iso_date(value: str, argument_name: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{argument_name} must be a valid date in YYYY-MM-DD format: {value}") from exc


def validate_date_range(from_date: str, to_date: str) -> None:
    start = parse_iso_date(from_date, "--from-date")
    end = parse_iso_date(to_date, "--to-date")
    if start > end:
        raise ValueError(f"--from-date must be on or before --to-date: {from_date} > {to_date}")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def polite_email() -> str | None:
    return os.getenv("CROSSREF_MAILTO") or os.getenv("OPENALEX_MAILTO") or os.getenv("UNPAYWALL_EMAIL")


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "utd-ft-journal-tracker/0.1 "
                f"(mailto:{polite_email() or 'set-UNPAYWALL_EMAIL@example.com'})"
            )
        }
    )
    return session


def get_json(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logging.warning("API request failed: %s params=%s error=%s", url, params, exc)
        return None
    except ValueError as exc:
        logging.warning("Invalid JSON from %s: %s", url, exc)
        return None


def load_journals(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    journals = data.get("journals", [])
    if not journals:
        raise ValueError(f"No journals found in {path}")
    return journals


def filter_journals(journals: list[dict[str, Any]], list_filter: str) -> list[dict[str, Any]]:
    """Return the journal subset requested by the command-line filter."""
    if list_filter == "UTD24":
        return [journal for journal in journals if journal.get("utd24") is True]
    if list_filter == "FT50":
        return [journal for journal in journals if journal.get("ft50") is True]
    if list_filter == "both":
        return [journal for journal in journals if journal.get("utd24") is True and journal.get("ft50") is True]
    if list_filter == "all-configured":
        return journals
    # Default: the UTD24/FT50 union. This intentionally skips optional watchlist
    # journals that are present in journals.yaml but not flagged for either list.
    return [journal for journal in journals if journal.get("utd24") is True or journal.get("ft50") is True]


def list_type(journal: dict[str, Any]) -> str:
    labels = []
    if journal.get("utd24"):
        labels.append("UTD24")
    if journal.get("ft50"):
        labels.append("FT50")
    return ";".join(labels)


def journal_name(journal: dict[str, Any]) -> str:
    return journal.get("journal_name") or journal.get("name", "")


def clean_text(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    value = re.sub(r"<[^>]+>", " ", str(value))
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def date_parts_to_iso(parts: dict[str, Any]) -> str:
    date_parts = parts.get("date-parts") or []
    if not date_parts or not date_parts[0]:
        return ""
    year, month, day = (date_parts[0] + [1, 1])[:3]
    return f"{year:04d}-{month:02d}-{day:02d}"


def publication_date(item: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "published", "issued"):
        date_value = date_parts_to_iso(item.get(key, {}))
        if date_value:
            return date_value
    return ""


def crossref_authors(item: dict[str, Any]) -> str:
    names = []
    for author in item.get("author", []):
        full_name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
        if full_name:
            names.append(full_name)
    return "; ".join(names)


def crossref_url(item: dict[str, Any]) -> str:
    if item.get("URL"):
        return item["URL"]
    doi = item.get("DOI")
    return f"https://doi.org/{doi}" if doi else ""


def fetch_crossref_articles(
    session: requests.Session,
    journal: dict[str, Any],
    from_date: str,
    to_date: str,
    rows: int,
    sleep: float,
) -> list[dict[str, Any]]:
    identifiers = []
    for key in ("issn", "eissn"):
        value = journal.get(key)
        if value and value not in identifiers:
            identifiers.append(value)
    if not identifiers:
        logging.warning("Skipping %s because no ISSN is configured", journal_name(journal))
        return []

    articles: list[dict[str, Any]] = []
    for issn in identifiers:
        url = f"https://api.crossref.org/journals/{issn}/works"
        cursor = "*"
        request_succeeded = False
        while True:
            params = {
                "filter": f"from-pub-date:{from_date},until-pub-date:{to_date},type:journal-article",
                "select": "DOI,title,author,container-title,abstract,published,published-print,published-online,issued,volume,issue,page,URL",
                "rows": rows,
                "cursor": cursor,
                "mailto": polite_email(),
            }
            params = {key: value for key, value in params.items() if value}
            data = get_json(session, url, params)
            if not data:
                break
            request_succeeded = True

            message = data.get("message", {})
            items = message.get("items", [])
            articles.extend(items)
            next_cursor = message.get("next-cursor")
            if not items or not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            time.sleep(sleep)
        if request_succeeded:
            break

    logging.info("%s: fetched %d Crossref records", journal_name(journal), len(articles))
    return articles


def reconstruct_openalex_abstract(work: dict[str, Any]) -> str:
    inverted = work.get("abstract_inverted_index")
    if not inverted:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        words.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(words))


def fetch_openalex(session: requests.Session, doi: str) -> dict[str, Any]:
    if not doi:
        return {}
    params = {"mailto": polite_email()} if polite_email() else None
    url = f"https://api.openalex.org/works/https://doi.org/{quote(doi.lower(), safe='')}"
    data = get_json(session, url, params)
    return data or {}


def openalex_details(work: dict[str, Any]) -> tuple[str, str, str, str]:
    affiliations = []
    topics = []
    is_oa = ""
    pdf_url = ""

    if work:
        for authorship in work.get("authorships", []):
            author_name = authorship.get("author", {}).get("display_name", "")
            institutions = [
                institution.get("display_name", "")
                for institution in authorship.get("institutions", [])
                if institution.get("display_name")
            ]
            if author_name and institutions:
                affiliations.append(f"{author_name}: {', '.join(institutions)}")
        topics = [topic.get("display_name", "") for topic in work.get("topics", []) if topic.get("display_name")]
        oa = work.get("open_access", {})
        is_oa = str(bool(oa.get("is_oa")))
        pdf_url = oa.get("oa_url") or ""

    return "; ".join(affiliations), "; ".join(topics), is_oa, pdf_url


def fetch_unpaywall_pdf(session: requests.Session, doi: str) -> tuple[str, str]:
    email = os.getenv("UNPAYWALL_EMAIL") or polite_email()
    if not doi or not email:
        return "", ""
    url = f"https://api.unpaywall.org/v2/{quote(doi)}"
    data = get_json(session, url, {"email": email})
    if not data:
        return "", ""
    best = data.get("best_oa_location") or {}
    pdf_url = best.get("url_for_pdf") or ""
    is_oa = str(bool(data.get("is_oa")))
    return is_oa, pdf_url


def make_record(
    journal: dict[str, Any],
    item: dict[str, Any],
    openalex_work: dict[str, Any],
    unpaywall_oa: str,
    unpaywall_pdf: str,
    fetched_at: str,
) -> dict[str, Any]:
    affiliations, topics, openalex_oa, openalex_pdf = openalex_details(openalex_work)
    abstract = clean_text(item.get("abstract")) or reconstruct_openalex_abstract(openalex_work)
    source_api = ["Crossref"]
    if openalex_work:
        source_api.append("OpenAlex")
    if unpaywall_oa or unpaywall_pdf:
        source_api.append("Unpaywall")

    return {
        "journal": journal_name(journal),
        "list_type": list_type(journal),
        "title": clean_text(item.get("title")),
        "authors": crossref_authors(item),
        "affiliations": affiliations,
        "abstract": clean_text(abstract),
        "doi": (item.get("DOI") or "").lower(),
        "publication_date": publication_date(item),
        "volume": item.get("volume", ""),
        "issue": item.get("issue", ""),
        "pages": item.get("page", ""),
        "article_url": crossref_url(item),
        "is_oa": unpaywall_oa or openalex_oa,
        "pdf_url": unpaywall_pdf or openalex_pdf,
        "source_api": "+".join(source_api),
        "fetched_at": fetched_at,
        "topics": topics,
    }


def load_existing(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["topics"])
    return pd.read_csv(csv_path, dtype=str).fillna("")


def merge_records(existing: pd.DataFrame, new_records: list[dict[str, Any]]) -> pd.DataFrame:
    new_df = pd.DataFrame(new_records)
    combined = pd.concat([existing, new_df], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["topics"])

    combined = combined.reindex(columns=EXCEL_COLUMNS + ["topics"]).fillna("")
    combined["doi"] = combined["doi"].astype(str).str.strip().str.lower()
    combined = combined.sort_values("fetched_at")

    # De-duplicate records with DOI by DOI. Keep no-DOI records only if they are
    # distinct on a conservative title+journal+date key, avoiding the common bug
    # where every blank DOI collapses into one row.
    with_doi = combined[combined["doi"].ne("")].drop_duplicates(subset=["doi"], keep="last")
    without_doi = combined[combined["doi"].eq("")].copy()
    if not without_doi.empty:
        key = (
            without_doi["title"].astype(str).str.strip().str.lower()
            + "|"
            + without_doi["journal"].astype(str).str.strip().str.lower()
            + "|"
            + without_doi["publication_date"].astype(str).str.strip().str.lower()
        )
        without_doi = without_doi.loc[~key.duplicated(keep="last")]

    return pd.concat([with_doi, without_doi], ignore_index=True).sort_values(
        ["journal", "publication_date", "title"], na_position="last"
    ).fillna("")


def bibtex_key(row: pd.Series) -> str:
    year = str(row.get("publication_date", ""))[:4] or "nodate"
    author_words = str(row.get("authors", "")).split(";")[0].split()
    title_words = str(row.get("title", "")).split()
    first_author = author_words[-1] if author_words else "anon"
    first_word = re.sub(r"[^A-Za-z0-9]+", "", title_words[0] if title_words else "article")
    return re.sub(r"[^A-Za-z0-9]+", "", f"{first_author}{year}{first_word}") or f"article{year}"


def escape_bibtex(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_bibtex(df: pd.DataFrame, path: Path) -> None:
    entries = []
    used_keys: dict[str, int] = {}
    for _, row in df.iterrows():
        key = bibtex_key(row)
        used_keys[key] = used_keys.get(key, 0) + 1
        if used_keys[key] > 1:
            key = f"{key}{used_keys[key]}"
        fields = {
            "title": row.get("title", ""),
            "author": str(row.get("authors", "")).replace("; ", " and "),
            "journal": row.get("journal", ""),
            "year": str(row.get("publication_date", ""))[:4],
            "volume": row.get("volume", ""),
            "number": row.get("issue", ""),
            "pages": row.get("pages", ""),
            "doi": row.get("doi", ""),
            "url": row.get("article_url", ""),
        }
        body = "\n".join(
            f"  {name} = {{{escape_bibtex(value)}}},"
            for name, value in fields.items()
            if str(value or "").strip()
        )
        entries.append(f"@article{{{key},\n{body}\n}}")
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")


def export_outputs(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "articles.csv"
    xlsx_path = output_dir / "articles.xlsx"
    latest_csv_path = output_dir / "latest_articles.csv"
    latest_xlsx_path = output_dir / "latest_articles.xlsx"
    bib_path = output_dir / "articles.bib"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_csv(latest_csv_path, index=False, encoding="utf-8-sig")
    df[EXCEL_COLUMNS].to_excel(xlsx_path, index=False)
    df[EXCEL_COLUMNS].to_excel(latest_xlsx_path, index=False)
    write_bibtex(df, bib_path)
    logging.info("Wrote %s, %s, %s, %s, and %s", csv_path, xlsx_path, latest_csv_path, latest_xlsx_path, bib_path)


def main() -> int:
    setup_logging()
    args = parse_args()
    try:
        validate_date_range(args.from_date, args.to_date)
    except ValueError as exc:
        logging.error(str(exc))
        return 2
    journals_path = Path(args.journals)
    output_dir = Path(args.output_dir)
    session = make_session()
    all_journals = load_journals(journals_path)
    journals = filter_journals(all_journals, args.list)
    existing = load_existing(output_dir / "articles.csv")
    existing_dois = set(existing["doi"].str.lower()) if "doi" in existing else set()
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_records: list[dict[str, Any]] = []

    logging.info(
        "Loaded %d configured journals; fetching %d journals for list=%s; existing DOI records=%d",
        len(all_journals),
        len(journals),
        args.list,
        len(existing_dois),
    )
    for journal in journals:
        for item in fetch_crossref_articles(session, journal, args.from_date, args.to_date, args.rows, args.sleep):
            doi = (item.get("DOI") or "").lower()
            if not doi or doi in existing_dois:
                continue
            openalex_work = fetch_openalex(session, doi)
            time.sleep(args.sleep)
            unpaywall_oa, unpaywall_pdf = fetch_unpaywall_pdf(session, doi)
            time.sleep(args.sleep)
            new_records.append(make_record(journal, item, openalex_work, unpaywall_oa, unpaywall_pdf, fetched_at))
            existing_dois.add(doi)

    combined = merge_records(existing, new_records)
    export_outputs(combined, output_dir)
    logging.info("Added %d new records; total records: %d", len(new_records), len(combined))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
