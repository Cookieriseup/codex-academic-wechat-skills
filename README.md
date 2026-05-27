# Codex Academic WeChat Skills

Codex skills for academic reading, journal tracking, and top-journal article monitoring.

- `journal-reading`: deep reading for a single academic paper, report, article, or comparable source.
- `journal-tracking`: journal issue tracking and multi-paper digest generation for two or more sources.
- `utd-ft50-journal-tracker`: UTD24/FT50 article tracking with Crossref/OpenAlex/Unpaywall metadata, validation reports, weekly briefs, topic tags, and Zotero BibTeX/RIS export.

The skills are designed for Chinese academic writing workflows, including Markdown notes, HTML reading reports, WeChat copy-ready drafts, Word-ready reports, journal/issue digests, NotebookLM handoff prompts, and weekly top-journal monitoring.

## Repository Layout

```text
skills/
  journal-reading/
    SKILL.md
    references/
    templates/
    agents/
    assets/
  journal-tracking/
    SKILL.md
    references/
    templates/
    agents/
    assets/
  utd-ft50-journal-tracker/
    SKILL.md
    references/
    scripts/
    agents/
docs/
  notebooklm_journal_reading_source.md
examples/
```

## What These Skills Do

`journal-reading` is triggered by one readable source, such as a PDF, DOI page, web article, abstract, or report. It asks Codex to extract bibliographic information, read the source in a structured order, explain methods and findings, preserve evidence boundaries, and produce public-facing Chinese drafts.

`journal-tracking` is triggered by two or more sources, such as multiple PDFs, a journal issue page, DOI list, screenshots, abstracts, or an online-first batch. It asks Codex to build a paper inventory, group papers by theme, and generate a phone-friendly journal tracking digest.

`utd-ft50-journal-tracker` is triggered by requests to set up or operate an automated UTD24/FT50 tracker. It bundles scripts for journal validation, Crossref/OpenAlex/Unpaywall fetching, duplicate checks, field-completeness reports, weekly Markdown reports, Chinese top-journal briefs, OA PDF downloads, and Zotero-compatible BibTeX/RIS exports. It gives special attention to AI, innovation, platforms, digital transformation, China samples, team science, research commercialization, intellectual property, and technology transfer.

The reading/tracking writing skills include a rule for quote-based analysis:

- single source: at least five short original excerpts with analysis;
- multiple sources: at least two short original excerpts per source with analysis;
- if only titles, metadata, or abstracts are available, the output must state the evidence boundary.

## Installation

Copy any skill folder into your Codex skills directory.

Example:

```text
<codex-skills-dir>/
  journal-reading/
  journal-tracking/
  utd-ft50-journal-tracker/
```

Then restart or refresh Codex so the skills are discovered.

## Customization

Before use, customize:

- footer signature fields in `SKILL.md`, `references/style_guide.md`, and the HTML templates;
- optional public-account QR image referenced as `assets/public_account_qr.png`;
- welcome lines, title prefixes, and account-specific wording;
- journal ranking terminology for your own field or publication standards.

Do not commit real PDFs, downloaded article pages, QR images, generated outputs, or private notes unless you have the right to publish them.

## NotebookLM

`docs/notebooklm_journal_reading_source.md` is a portable instruction file that can be uploaded into NotebookLM together with source papers. It mirrors the journal-reading workflow, including evidence boundaries, quote-analysis rules, and audio overview prompts.

## Privacy

This public package intentionally excludes:

- real PDF files;
- generated reports and WeChat drafts;
- generated tracker outputs and downloaded PDFs;
- real QR images;
- downloaded WeChat article caches;
- local absolute paths;
- personal names or institution-specific signatures.

See `PRIVACY.md` for the release checklist.

## License

MIT License. See `LICENSE`.
