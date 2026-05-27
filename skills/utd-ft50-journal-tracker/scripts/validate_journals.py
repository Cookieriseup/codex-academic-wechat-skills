#!/usr/bin/env python
"""Validate journal configuration and write a Markdown acceptance report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
JOURNALS_PATH = ROOT / "journals.yaml"
REPORT_PATH = ROOT / "validation_report.md"
REQUIRED_FIELDS = ("journal_name", "publisher", "utd24", "ft50", "homepage_url", "source_url")
EXPECTED_UTD_ONLY = {"INFORMS Journal on Computing"}
FT50_2026_ADDED = {"Academy of Management Annals", "American Sociological Review", "Psychological Science"}
FT50_2026_REMOVED = {"Human Relations", "Journal of Business Ethics", "Organization Studies"}
EXPECTED_UNION_COUNT = 51


def load_journals() -> list[dict[str, Any]]:
    with JOURNALS_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("journals", [])


def missing_fields(journal: dict[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_FIELDS if field not in journal or journal[field] in (None, "")]
    if not journal.get("issn") and not journal.get("eissn"):
        missing.append("issn/eissn")
    return missing


def status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> int:
    journals = load_journals()
    missing_by_journal = {
        journal.get("journal_name", "<missing journal_name>"): missing_fields(journal)
        for journal in journals
        if missing_fields(journal)
    }
    utd_count = sum(1 for journal in journals if journal.get("utd24") is True)
    ft_count = sum(1 for journal in journals if journal.get("ft50") is True)
    by_name = {journal.get("journal_name", ""): journal for journal in journals}
    utd_only = {journal["journal_name"] for journal in journals if journal.get("utd24") and not journal.get("ft50")}
    active_union_count = sum(1 for journal in journals if journal.get("utd24") or journal.get("ft50"))
    ft50_2026_added_ok = all(by_name.get(name, {}).get("ft50") is True for name in FT50_2026_ADDED)
    ft50_2026_removed_ok = all(by_name.get(name, {}).get("ft50") is False for name in FT50_2026_REMOVED)

    checks = [
        ("All journals contain required fields", not missing_by_journal),
        ("UTD24 count is 24", utd_count == 24),
        ("FT50 count is 50", ft_count == 50),
        ("UTD24/FT50 active union count is 51", active_union_count == EXPECTED_UNION_COUNT),
        ("2026 FT50 added journals are marked FT50", ft50_2026_added_ok),
        ("2026 FT50 removed journals are not marked FT50", ft50_2026_removed_ok),
        ("Only INFORMS Journal on Computing is UTD24-only", utd_only == EXPECTED_UTD_ONLY),
    ]
    ok = all(result for _, result in checks)

    lines = [
        "# Journal Configuration Validation Report",
        "",
        f"- Total configured journals: {len(journals)}",
        f"- UTD24 count: {utd_count}",
        f"- FT50 count: {ft_count}",
        f"- Active UTD24/FT50 union count: {active_union_count}",
        f"- Overall status: {status(ok)}",
        "",
        "## Checks",
        "",
        "| Check | Status |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name} | {status(result)} |" for name, result in checks)
    lines.extend(["", "## UTD24-Only Journals", "", ", ".join(sorted(utd_only)) or "None"])
    lines.extend([
        "",
        "## 2026 FT50 Change Check",
        "",
        "Added and marked FT50: " + ", ".join(sorted(FT50_2026_ADDED)),
        "Retained as optional watchlist but not marked FT50: " + ", ".join(sorted(FT50_2026_REMOVED)),
    ])

    if missing_by_journal:
        lines.extend(["", "## Missing Fields", "", "| Journal | Missing fields |", "| --- | --- |"])
        lines.extend(
            f"| {journal_name} | {', '.join(fields)} |"
            for journal_name, fields in sorted(missing_by_journal.items())
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
