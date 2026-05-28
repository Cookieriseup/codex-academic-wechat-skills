---
name: utd-ft50-journal-tracker
description: Build, validate, run, and maintain a Python tracker for UTD24 and Financial Times FT50 journal articles. Use when the user asks to track top business-school journals, fetch new articles from Crossref/OpenAlex/Unpaywall, validate UTD24/FT50 journal configuration, generate weekly top-journal briefs, tag AI/innovation/platform/digital transformation/China sample topics, export Zotero BibTeX/RIS, or download only legally available open-access PDFs.
---

# UTD/FT50 Journal Tracker

## Purpose

Use this skill to create or operate a local Python project that tracks UTD24 and FT50 journal articles. The bundled scripts implement:

- journal configuration validation for UTD24=24, FT50=50, active union=51;
- Crossref metadata fetching by ISSN and date range;
- OpenAlex enrichment for affiliations, OA status, abstracts, and topics;
- Unpaywall lookup for legal OA PDF URLs;
- CSV, Excel, BibTeX, and RIS exports;
- duplicate and field-completeness reports;
- weekly Markdown reports and Chinese top-journal tracking briefs;
- special tagging for team science, research commercialization, intellectual property, and technology transfer;
- optional OA PDF downloading from already-recorded `pdf_url` values only;
- campus IP institutional downloading with Python proxy inheritance disabled;
- manual browser download queues and local PDF reconciliation for captcha or institutional-login cases.

## Project Setup

When creating a tracker project, make the target folder contain:

```text
journals.yaml
requirements.txt
scripts/
outputs/
```

Copy the bundled files:

- `references/journals.yaml` -> project `journals.yaml`
- `references/requirements.txt` -> project `requirements.txt`
- all `scripts/*.py` -> project `scripts/`

Then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Recommended environment variables:

```powershell
$env:UNPAYWALL_EMAIL="your_email@example.com"
$env:CROSSREF_MAILTO="your_email@example.com"
$env:OPENALEX_MAILTO="your_email@example.com"
```

## Core Commands

Run the acceptance checks:

```powershell
python scripts\validate_journals.py
python scripts\smoke_test.py
python scripts\check_duplicates.py
python scripts\field_completeness_report.py
```

Fetch a date range:

```powershell
python scripts\update_articles.py --from-date 2026-04-01 --to-date 2026-04-30
```

Default `update_articles.py` behavior fetches only the active UTD24/FT50 union. Use `--list all-configured` only when the user explicitly wants optional watchlist journals too.

Run the weekly workflow:

```powershell
python scripts\weekly_update.py
python scripts\generate_weekly_brief.py
```

Download legal OA PDFs that are already listed in outputs:

```powershell
python scripts\download_oa_pdfs.py --limit 20
```

Check Python network/proxy behavior and campus access:

```powershell
python scripts\check_network_access.py --doi 10.1287/isre.2023.0561 --access-mode campus_ip
```

Download institutionally accessible PDFs through campus IP:

```powershell
python scripts\download_institutional_pdfs.py --access-mode campus_ip --limit 20
```

If a publisher returns HTML, 401/403, a login page, or a captcha page, export a manual browser queue instead:

```powershell
python scripts\export_manual_pdf_queue.py
```

After the user downloads authorized PDFs in a browser, reconcile them locally:

```powershell
python scripts\reconcile_manual_pdfs.py --pdf-dir "$HOME\Downloads"
python scripts\reconcile_manual_pdfs.py --pdf-dir "$HOME\Downloads" --copy
```

## Outputs

Main outputs:

- `outputs/articles.csv`
- `outputs/articles.xlsx`
- `outputs/latest_articles.csv`
- `outputs/latest_articles.xlsx`
- `outputs/articles.bib`

Weekly outputs:

- `outputs/weekly_report.md`
- `outputs/weekly_top_journal_brief.md`
- `outputs/weekly/weekly_latest_articles.csv`
- `outputs/weekly/weekly_latest_articles.xlsx`
- `outputs/weekly/weekly_latest_articles.bib`
- `outputs/weekly/weekly_latest_articles.ris`

Validation outputs:

- `validation_report.md`
- `duplicate_report.md`
- `outputs/field_completeness_report.xlsx`
- `outputs/smoke_test_latest_articles.xlsx`
- `outputs/manual_pdf_download_queue.xlsx`
- `outputs/manual_pdf_download_queue.csv`
- `outputs/manual_pdfs/manual_pdf_reconcile_log.csv`

## Topic and Relevance Rules

The weekly workflow tags:

- `AI`
- `innovation`
- `platform`
- `digital transformation`
- `China sample`
- `team science`
- `research commercialization`
- `intellectual property`
- `technology transfer`

It marks research relevance using transparent keyword rules around cross-border R&D, innovation policy, technology transfer, institutional/regulatory context, China, platforms, AI, digital transformation, team science, research commercialization, intellectual property, patents, licensing, university spin-offs, and university-industry links. Treat these as screening heuristics, not final literature review judgments.

Always give special attention to articles involving:

- 团队科学学 / team science / scientific collaboration / research teams;
- 科技成果转化 / research commercialization / technology commercialization / university spin-offs;
- 知识产权 / intellectual property / patents / licensing;
- 技术转移 / technology transfer / knowledge transfer / university-industry collaboration.

## Compliance Rules

- Do not bypass paywalls.
- Do not scrape institutional access.
- For campus IP access, use `requests.Session.trust_env = False` and no proxies so Python does not inherit `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY`.
- If a VPN/TUN adapter controls the default route, `trust_env=False` prevents proxy env inheritance but cannot override the OS route; the user may need VPN split tunneling or to disconnect VPN for true campus-IP downloads.
- Save or download PDFs only when `pdf_url` is supplied by Unpaywall/OpenAlex or otherwise clearly legal and open access.
- For institutional downloads, save a file only if the publisher returns an actual PDF. Do not save HTML, login pages, captcha pages, 401, or 403 responses.
- If human verification, school login, or captcha is required, generate a manual browser download queue. Do not automate or bypass that verification.
- Reconcile only PDFs the user has manually downloaded through legitimate browser access; never infer that a failed automated download means the article is unavailable.
- If a record has only title/metadata, do not imply that full text was read.
- If Crossref/OpenAlex returns 404 for an item, keep the available metadata and continue.

## Common Fixes

- If a user supplies `2026-04-31`, correct it to `2026-04-30`; the scripts validate date strings before fetching.
- If `gh` is unavailable, use normal `git` or zip-based workflows.
- If optional watchlist journals appear in results, check that the run did not use `--list all-configured`.
- If no weekly records appear, verify the date window and publisher deposit timing; Crossref may lag.
