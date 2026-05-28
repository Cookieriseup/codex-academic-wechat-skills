# UTD24 and FT50 Journal Article Tracker

This project tracks recent articles from UTD24 and Financial Times FT50 business-school journals.

It uses:

- Crossref REST API for journal-article metadata by ISSN and publication date.
- OpenAlex API for author institutions, open-access status, abstract reconstruction, and topic metadata.
- Unpaywall API for legal open-access PDF links only.

The tracker does not bypass paywalls. PDF URLs are saved only when Unpaywall or OpenAlex reports a legal open-access location. The optional downloader only downloads URLs already recorded in `pdf_url`.

## Setup

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

Unpaywall expects an email parameter. Crossref and OpenAlex also prefer polite API clients with contact emails.

## Run

Default run: fetch the active UTD24/FT50 union only. Optional watchlist journals in `journals.yaml` are skipped unless `--list all-configured` is used.

```powershell
python scripts/update_articles.py --from-date 2026-01-01 --to-date 2026-05-31
```

Subset examples:

```powershell
python scripts/update_articles.py --from-date 2026-01-01 --to-date 2026-05-31 --list UTD24
python scripts/update_articles.py --from-date 2026-01-01 --to-date 2026-05-31 --list FT50
python scripts/update_articles.py --from-date 2026-01-01 --to-date 2026-05-31 --list both
python scripts/update_articles.py --from-date 2026-01-01 --to-date 2026-05-31 --list all-configured
```

Outputs are written to `outputs/`:

- `articles.csv`
- `articles.xlsx`
- `latest_articles.csv` alias for downstream scripts
- `latest_articles.xlsx` alias for downstream scripts
- `articles.bib`

## Excel Columns

The Excel export includes:

`journal`, `list_type`, `title`, `authors`, `affiliations`, `abstract`, `doi`, `publication_date`, `volume`, `issue`, `pages`, `article_url`, `is_oa`, `pdf_url`, `source_api`, `fetched_at`.

The CSV also keeps a `topics` column from OpenAlex for downstream filtering.

## Incremental Updates

The script reads `outputs/articles.csv` before fetching. Existing DOI values are skipped. Records with DOI are de-duplicated by DOI; records without DOI are de-duplicated conservatively by `title + journal + publication_date`.

## Journal Configuration

`journals.yaml` stores each journal's:

- journal name
- ISSN and EISSN
- publisher
- UTD24 membership
- FT50 membership
- website URL
- RSS or table-of-contents URL

FT50 flags follow the 2026 Financial Times update. `Academy of Management Annals`, `American Sociological Review`, and `Psychological Science` are marked as FT50. `Human Relations`, `Journal of Business Ethics`, and `Organization Studies` are retained as optional watchlist journals but are not marked as FT50.

Some publishers expose stable RSS feeds; others only expose table-of-contents pages. Crossref ISSN fetching is the primary article discovery path in the current implementation.

## Acceptance Checks

Validate journal configuration:

```powershell
python scripts/validate_journals.py
```

This writes `validation_report.md` and checks required `journals.yaml` fields, UTD24 count, FT50 count, active union count, the 2026 FT50 added/removed journal flags, and the UTD24-only journal rule.

Run a small live API smoke test:

```powershell
python scripts/smoke_test.py
```

This tests Management Science, Journal of Marketing, Organization Science, Research Policy, and INFORMS Journal on Computing for the latest 90 days, with at most 10 articles per journal. It writes `outputs/smoke_test_latest_articles.xlsx` with article rows and field missing rates.

Check duplicate records:

```powershell
python scripts/check_duplicates.py
```

This checks `outputs/latest_articles.csv` or `outputs/latest_articles.xlsx` when present, falling back to `outputs/articles.csv` or `outputs/articles.xlsx`. It writes `duplicate_report.md`.

Generate field completeness report:

```powershell
python scripts/field_completeness_report.py
```

This writes `outputs/field_completeness_report.xlsx` with per-journal completeness rates for title, authors, abstract, DOI, publication date, article URL, PDF URL, and affiliations.

## Download Legal OA PDFs

After articles are fetched, download legal open-access PDFs listed in the `pdf_url` column:

```powershell
python scripts/download_oa_pdfs.py --limit 20
```

Downloaded PDFs and `download_log.csv` are saved under `outputs/pdfs/`. This script does not search for paywalled PDFs and does not bypass access controls.

## Campus IP Direct Download

Codex/ChatGPT can use a VPN or browser proxy for normal interaction. Paper downloads are different: when you are on campus, publisher access may depend on the school's campus IP. In that case, run download scripts locally and avoid letting Python inherit system proxy settings.

Check how Python reaches a DOI or article URL:

```powershell
python scripts/check_network_access.py --doi 10.1287/isre.2023.0561 --access-mode campus_ip
```

`campus_ip` mode uses `requests.Session.trust_env = False` and an empty proxy dictionary, so Python ignores `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and related environment variables.

Download PDFs only when the publisher returns an actual PDF through direct campus access:

```powershell
python scripts/download_institutional_pdfs.py --access-mode campus_ip --limit 20
```

The institutional downloader tries `publisher_pdf_url`, `doi_url`, or `article_url` when present. If the response is HTML, a login page, 401/403, or a captcha page, it does not save the file and records the failure reason in `outputs/institutional_pdfs/institutional_download_log.csv`.

If the publisher requires browser verification, institutional login, or captcha completion, use a manual queue instead of trying to automate that step:

```powershell
python scripts/export_manual_pdf_queue.py
```

This writes `outputs/manual_pdf_download_queue.xlsx` and `outputs/manual_pdf_download_queue.csv`. Open the article links in your browser, complete any required school login or human verification, and download only PDFs you are authorized to access.

After manual browser downloads, reconcile local PDFs back to the queue:

```powershell
python scripts/reconcile_manual_pdfs.py --pdf-dir "$HOME\Downloads"
python scripts/reconcile_manual_pdfs.py --pdf-dir "$HOME\Downloads" --copy
```

The first command is a dry run. The second copies matched PDFs into `outputs/manual_pdfs/matched/` and writes `outputs/manual_pdfs/manual_pdf_reconcile_log.csv`.

Do not use this project to bypass paywalls. Only use PDFs available through legitimate open access or your school's authorized campus subscription.

## Weekly Update

Run the weekly workflow manually:

```powershell
python scripts/weekly_update.py
```

By default this fetches the last 7 days for the active UTD24/FT50 union, merges new records into the master outputs, and writes:

- `outputs/weekly_report.md`
- `outputs/weekly/weekly_latest_articles.csv`
- `outputs/weekly/weekly_latest_articles.xlsx`
- `outputs/weekly/weekly_latest_articles.bib`
- `outputs/weekly/weekly_latest_articles.ris`

The weekly report tags articles with transparent keyword rules for `AI`, `innovation`, `platform`, `digital transformation`, and `China sample`. It also marks research-relevant articles using keywords around cross-border R&D, innovation policy, digital transformation, platform strategy, China, institutions, and technology transfer.

Use an explicit range when needed:

```powershell
python scripts/weekly_update.py --from-date 2026-05-20 --to-date 2026-05-27
```

Both BibTeX and RIS files can be imported into Zotero.

Generate a Chinese reading brief from the latest weekly output:

```powershell
python scripts/generate_weekly_brief.py
```

This writes `outputs/weekly_top_journal_brief.md` with a one-paragraph overview, theme counts, top journal sources, recommended priority reads, and the full weekly list.
