#!/usr/bin/env python
"""Run a small live API smoke test for selected journals."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_articles import (  # noqa: E402
    EXCEL_COLUMNS,
    fetch_openalex,
    fetch_unpaywall_pdf,
    get_json,
    journal_name,
    load_journals,
    make_record,
    make_session,
    polite_email,
    setup_logging,
)

SMOKE_JOURNALS = {
    "Management Science",
    "Journal of Marketing",
    "Organization Science",
    "Research Policy",
    "INFORMS Journal on Computing",
}
OUTPUT_PATH = ROOT / "outputs" / "smoke_test_latest_articles.xlsx"


def fetch_crossref_smoke_page(session, journal: dict, from_date: str, to_date: str) -> list[dict]:
    for issn in (journal.get("issn"), journal.get("eissn")):
        if not issn:
            continue
        data = get_json(
            session,
            f"https://api.crossref.org/journals/{issn}/works",
            {
                "filter": f"from-pub-date:{from_date},until-pub-date:{to_date},type:journal-article",
                "select": "DOI,title,author,container-title,abstract,published,published-print,published-online,issued,volume,issue,page,URL",
                "rows": 10,
                "mailto": polite_email(),
            },
        )
        if data:
            return data.get("message", {}).get("items", [])[:10]
    return []


def missing_rates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    for column in EXCEL_COLUMNS:
        missing = int(df[column].fillna("").eq("").sum()) if column in df else total
        rows.append(
            {
                "field": column,
                "missing_count": missing,
                "total_count": total,
                "missing_rate": missing / total if total else 0,
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    setup_logging()
    session = make_session()
    journals = [journal for journal in load_journals(ROOT / "journals.yaml") if journal_name(journal) in SMOKE_JOURNALS]
    missing = sorted(SMOKE_JOURNALS - {journal_name(journal) for journal in journals})
    if missing:
        raise ValueError(f"Smoke-test journals missing from journals.yaml: {', '.join(missing)}")

    to_date = date.today()
    from_date = to_date - timedelta(days=90)
    fetched_at = pd.Timestamp.utcnow().isoformat()
    records = []

    for journal in journals:
        items = fetch_crossref_smoke_page(session, journal, from_date.isoformat(), to_date.isoformat())
        for item in items:
            doi = (item.get("DOI") or "").lower()
            openalex_work = fetch_openalex(session, doi) if doi else {}
            unpaywall_oa, unpaywall_pdf = fetch_unpaywall_pdf(session, doi) if doi else ("", "")
            records.append(make_record(journal, item, openalex_work, unpaywall_oa, unpaywall_pdf, fetched_at))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records).reindex(columns=EXCEL_COLUMNS + ["topics"]).fillna("")
    with pd.ExcelWriter(OUTPUT_PATH) as writer:
        df[EXCEL_COLUMNS].to_excel(writer, sheet_name="latest_articles", index=False)
        missing_rates(df).to_excel(writer, sheet_name="missing_rates", index=False)

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
