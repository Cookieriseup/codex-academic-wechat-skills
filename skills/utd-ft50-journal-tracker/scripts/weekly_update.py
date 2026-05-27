#!/usr/bin/env python
"""Weekly UTD24/FT50 update with topic tags, relevance screening, BibTeX, and RIS."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_articles import (  # noqa: E402
    EXCEL_COLUMNS,
    fetch_crossref_articles,
    fetch_openalex,
    fetch_unpaywall_pdf,
    filter_journals,
    journal_name,
    load_existing,
    load_journals,
    make_record,
    make_session,
    merge_records,
    parse_iso_date,
    polite_email,
    publication_date,
    setup_logging,
    validate_date_range,
    write_bibtex,
)

OUTPUT_DIR = ROOT / "outputs"
WEEKLY_DIR = OUTPUT_DIR / "weekly"
WEEKLY_REPORT_PATH = OUTPUT_DIR / "weekly_report.md"
WEEKLY_CSV_PATH = WEEKLY_DIR / "weekly_latest_articles.csv"
WEEKLY_XLSX_PATH = WEEKLY_DIR / "weekly_latest_articles.xlsx"
WEEKLY_BIB_PATH = WEEKLY_DIR / "weekly_latest_articles.bib"
WEEKLY_RIS_PATH = WEEKLY_DIR / "weekly_latest_articles.ris"
MASTER_CSV_PATH = OUTPUT_DIR / "articles.csv"

THEME_KEYWORDS = {
    "AI": [
        r"\bAI\b",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "algorithmic",
        "generative ai",
        "large language model",
        r"\bLLM\b",
    ],
    "innovation": [
        "innovation",
        "innovative",
        "technology development",
        "r&d",
        "research and development",
        "patent",
        "knowledge spillover",
    ],
    "platform": [
        "platform",
        "ecosystem",
        "two-sided market",
        "marketplace",
        "app store",
        "digital platform",
    ],
    "digital transformation": [
        "digital transformation",
        "digitalization",
        "digitization",
        "digital technology",
        "digital economy",
        "data analytics",
    ],
    "China sample": [
        "china",
        "chinese",
        "prc",
        "mainland china",
        "hong kong",
        "shenzhen",
        "shanghai",
        "beijing",
    ],
    "team science": [
        "team science",
        "scientific team",
        "research team",
        "team collaboration",
        "collaboration network",
        "interdisciplinary team",
        "scientific collaboration",
        "团队科学",
        "科研团队",
        "团队合作",
        "跨学科团队",
    ],
    "research commercialization": [
        "research commercialization",
        "technology commercialization",
        "commercialization of research",
        "commercialisation of research",
        "science commercialization",
        "university spin-off",
        "academic spin-off",
        "成果转化",
        "科技成果转化",
        "科研成果转化",
        "技术商业化",
    ],
    "intellectual property": [
        "intellectual property",
        "patent",
        "patents",
        "trademark",
        "copyright",
        "licensing",
        "ip rights",
        "知识产权",
        "专利",
        "商标",
        "许可",
    ],
    "technology transfer": [
        "technology transfer",
        "knowledge transfer",
        "technology licensing",
        "university-industry",
        "industry-university",
        "science-industry",
        "sino-soviet alliance",
        "技术转移",
        "知识转移",
        "产学研",
        "大学-产业",
    ],
}

RESEARCH_RELEVANCE_KEYWORDS = {
    "cross-border R&D/policy": [
        "cross-border",
        "international business",
        "foreign direct investment",
        "multinational",
        "global value chain",
        "knowledge transfer",
        "technology transfer",
        "r&d",
        "research and development",
        "innovation policy",
        "industrial policy",
        "science and technology policy",
        "institutional",
        "regulation",
        "government",
        "china",
        "chinese",
        "digital transformation",
        "platform",
        "artificial intelligence",
        "team science",
        "scientific collaboration",
        "research commercialization",
        "technology commercialization",
        "technology transfer",
        "knowledge transfer",
        "intellectual property",
        "patent",
        "licensing",
        "university spin-off",
        "academic spin-off",
    ]
}


def parse_args() -> argparse.Namespace:
    today = date.today()
    default_from = today - timedelta(days=7)
    parser = argparse.ArgumentParser(description="Run weekly UTD24/FT50 article update.")
    parser.add_argument("--from-date", default=default_from.isoformat(), help="Start date, YYYY-MM-DD.")
    parser.add_argument("--to-date", default=today.isoformat(), help="End date, YYYY-MM-DD.")
    parser.add_argument("--rows", type=int, default=100, help="Crossref page size per request.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API calls in seconds.")
    parser.add_argument("--list", choices=["union", "UTD24", "FT50", "both"], default="union")
    return parser.parse_args()


def haystack(row: pd.Series) -> str:
    fields = ["title", "abstract", "topics", "journal", "authors", "affiliations"]
    return " ".join(str(row.get(field, "") or "") for field in fields).lower()


def matches_any(text: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if pattern.startswith("\\") or "\\b" in pattern:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
        elif pattern.lower() in text:
            return True
    return False


def annotate_weekly_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["theme_tags"] = []
        df["relevance_tags"] = []
        df["is_research_relevant"] = []
        return df

    annotated = df.copy()
    theme_values = []
    relevance_values = []
    relevant_values = []
    for _, row in annotated.iterrows():
        text = haystack(row)
        themes = [theme for theme, patterns in THEME_KEYWORDS.items() if matches_any(text, patterns)]
        relevance = [
            label for label, patterns in RESEARCH_RELEVANCE_KEYWORDS.items() if matches_any(text, patterns)
        ]
        theme_values.append("; ".join(themes))
        relevance_values.append("; ".join(relevance))
        relevant_values.append(bool(relevance or themes))

    annotated["theme_tags"] = theme_values
    annotated["relevance_tags"] = relevance_values
    annotated["is_research_relevant"] = relevant_values
    return annotated


def escape_ris(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def write_ris(df: pd.DataFrame, path: Path) -> None:
    entries = []
    for _, row in df.iterrows():
        lines = ["TY  - JOUR"]
        if row.get("title"):
            lines.append(f"TI  - {escape_ris(row.get('title'))}")
        for author in str(row.get("authors", "")).split("; "):
            if author.strip():
                lines.append(f"AU  - {escape_ris(author)}")
        if row.get("journal"):
            lines.append(f"JO  - {escape_ris(row.get('journal'))}")
        if row.get("publication_date"):
            lines.append(f"PY  - {escape_ris(str(row.get('publication_date'))[:4])}")
            lines.append(f"Y1  - {escape_ris(row.get('publication_date'))}")
        if row.get("volume"):
            lines.append(f"VL  - {escape_ris(row.get('volume'))}")
        if row.get("issue"):
            lines.append(f"IS  - {escape_ris(row.get('issue'))}")
        if row.get("pages"):
            lines.append(f"SP  - {escape_ris(row.get('pages'))}")
        if row.get("doi"):
            lines.append(f"DO  - {escape_ris(row.get('doi'))}")
        if row.get("article_url"):
            lines.append(f"UR  - {escape_ris(row.get('article_url'))}")
        if row.get("abstract"):
            lines.append(f"AB  - {escape_ris(row.get('abstract'))}")
        keywords = "; ".join(
            value for value in [row.get("theme_tags", ""), row.get("relevance_tags", ""), row.get("topics", "")]
            if str(value or "").strip()
        )
        if keywords:
            lines.append(f"KW  - {escape_ris(keywords)}")
        lines.append("ER  -")
        entries.append("\n".join(lines))
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")


def write_weekly_report(df: pd.DataFrame, from_date: str, to_date: str, path: Path) -> None:
    total = len(df)
    relevant = int(df["is_research_relevant"].sum()) if "is_research_relevant" in df else 0
    theme_counts = {}
    for tags in df.get("theme_tags", pd.Series(dtype=str)).fillna(""):
        for tag in [item.strip() for item in str(tags).split(";") if item.strip()]:
            theme_counts[tag] = theme_counts.get(tag, 0) + 1

    lines = [
        "# Weekly UTD24/FT50 Article Report",
        "",
        f"- Date range: {from_date} to {to_date}",
        f"- Generated at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Total new records: {total}",
        f"- Research-relevant records: {relevant}",
        f"- Zotero BibTeX: {WEEKLY_BIB_PATH}",
        f"- Zotero RIS: {WEEKLY_RIS_PATH}",
        "",
        "## Theme Counts",
        "",
        "| Theme | Count |",
        "| --- | ---: |",
    ]
    if theme_counts:
        lines.extend(f"| {theme} | {count} |" for theme, count in sorted(theme_counts.items()))
    else:
        lines.append("| None | 0 |")

    relevant_df = df[df["is_research_relevant"] == True] if "is_research_relevant" in df else df.iloc[0:0]
    lines.extend(["", "## Research-Relevant Articles", ""])
    if relevant_df.empty:
        lines.append("No research-relevant articles matched the current keyword rules.")
    else:
        for _, row in relevant_df.head(30).iterrows():
            title = row.get("title", "")
            journal = row.get("journal", "")
            date_value = row.get("publication_date", "")
            tags = row.get("theme_tags", "") or row.get("relevance_tags", "")
            doi = row.get("doi", "")
            url = row.get("article_url", "")
            lines.extend(
                [
                    f"### {title}",
                    "",
                    f"- Journal: {journal}",
                    f"- Date: {date_value}",
                    f"- Tags: {tags or 'None'}",
                    f"- DOI: {doi or 'N/A'}",
                    f"- URL: {url or 'N/A'}",
                    "",
                ]
            )

    lines.extend(["## All Weekly Articles", ""])
    if df.empty:
        lines.append("No new articles were fetched for this period.")
    else:
        lines.extend(["| Journal | Date | Title | Tags |", "| --- | --- | --- | --- |"])
        for _, row in df.iterrows():
            title = str(row.get("title", "")).replace("|", "\\|")
            lines.append(
                f"| {row.get('journal', '')} | {row.get('publication_date', '')} | {title} | {row.get('theme_tags', '')} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fetch_weekly_records(args: argparse.Namespace) -> list[dict[str, Any]]:
    session = make_session()
    journals = filter_journals(load_journals(ROOT / "journals.yaml"), args.list)
    existing = load_existing(MASTER_CSV_PATH)
    existing_dois = set(existing["doi"].astype(str).str.lower()) if "doi" in existing else set()
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records: list[dict[str, Any]] = []
    start_date = parse_iso_date(args.from_date, "--from-date").date()
    end_date = parse_iso_date(args.to_date, "--to-date").date()

    logging.info("Weekly update fetching %d journals for list=%s", len(journals), args.list)
    for journal in journals:
        items = fetch_crossref_articles(
            session=session,
            journal=journal,
            from_date=args.from_date,
            to_date=args.to_date,
            rows=args.rows,
            sleep=args.sleep,
        )
        for item in items:
            item_date = publication_date(item)
            if item_date:
                parsed_item_date = parse_iso_date(item_date, "publication_date").date()
                if parsed_item_date < start_date or parsed_item_date > end_date:
                    continue
            doi = (item.get("DOI") or "").lower()
            if doi and doi in existing_dois:
                continue
            openalex_work = fetch_openalex(session, doi) if doi else {}
            time.sleep(args.sleep)
            unpaywall_oa, unpaywall_pdf = fetch_unpaywall_pdf(session, doi) if doi else ("", "")
            time.sleep(args.sleep)
            records.append(make_record(journal, item, openalex_work, unpaywall_oa, unpaywall_pdf, fetched_at))
            if doi:
                existing_dois.add(doi)
    return records


def export_weekly_outputs(weekly_df: pd.DataFrame) -> None:
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    weekly_df.to_csv(WEEKLY_CSV_PATH, index=False, encoding="utf-8-sig")
    weekly_df.to_excel(WEEKLY_XLSX_PATH, index=False)
    write_bibtex(weekly_df, WEEKLY_BIB_PATH)
    write_ris(weekly_df, WEEKLY_RIS_PATH)

    existing = load_existing(MASTER_CSV_PATH)
    combined = merge_records(existing, weekly_df.to_dict("records"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_DIR / "articles.csv", index=False, encoding="utf-8-sig")
    combined.to_csv(OUTPUT_DIR / "latest_articles.csv", index=False, encoding="utf-8-sig")
    combined[EXCEL_COLUMNS].to_excel(OUTPUT_DIR / "articles.xlsx", index=False)
    combined[EXCEL_COLUMNS].to_excel(OUTPUT_DIR / "latest_articles.xlsx", index=False)
    write_bibtex(combined, OUTPUT_DIR / "articles.bib")


def main() -> int:
    setup_logging()
    args = parse_args()
    try:
        validate_date_range(args.from_date, args.to_date)
    except ValueError as exc:
        logging.error(str(exc))
        return 2

    records = fetch_weekly_records(args)
    weekly_df = pd.DataFrame(records).reindex(columns=EXCEL_COLUMNS + ["topics"]).fillna("")
    weekly_df = annotate_weekly_records(weekly_df)
    export_weekly_outputs(weekly_df)
    write_weekly_report(weekly_df, args.from_date, args.to_date, WEEKLY_REPORT_PATH)
    logging.info("Wrote weekly outputs and %s", WEEKLY_REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
