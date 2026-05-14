---
name: journal-reading
description: Use when the user wants to read, explain, compare, or turn academic journal articles into Chinese Markdown notes, Word-ready reports, seminar briefings, or WeChat public-account drafts. Handles PDFs, DOIs, URLs, screenshots, abstracts, existing notes, and journal-issue digests across management, psychology, AI, economics, library/information science, and intellectual property management.
---

# Journal Reading

## Goal

Turn selected academic articles into rigorous, readable Chinese outputs for:

- personal reading notes;
- HTML reading reports or WeChat preview drafts;
- seminar or group-meeting reports;
- WeChat public-account sharing drafts;
- multi-paper comparison or journal-issue digests.

Keep professional terms in English on first mention, with concise Chinese explanation when useful. Do not invent bibliographic data, findings, statistics, limitations, or citations.

## Inputs

Accept PDF, DOI, URL, screenshot, abstract text, existing notes, or a folder of papers. If the source is a PDF/URL not provided in text, extract enough content before writing. If access fails or only an abstract is available, state the evidence boundary.

For journal-issue or multi-paper inputs, produce a digest. For a single paper, produce a deep reading report unless the user asks for a short summary.

## Default Trigger

In the `journal-reading` project, when the user provides a single readable academic PDF and asks to analyze/read/summarize it, default to this task without requiring the user to restate it:

`Use $journal-reading to read this paper and output an HTML reading report, a WeChat HTML draft, and a Word report.`

Apply this default only when the PDF text and figures are readable enough to extract article content. If the PDF is scanned, image-only, encrypted, corrupted, or has unreadable figures/tables, first report the extraction boundary and ask whether to proceed with OCR or a limited abstract/title-based reading.

Default single-PDF outputs:

- `article_reading_note.md`
- `article_reading_report.html`
- `wechat_draft.html`
- `wechat_article_inline.html`
- `wechat_article_copy_ready.html`
- `cover_image.png`
- `article_reading_report.docx`
- optional `wechat_draft.md` if useful for later conversion

## Core Workflow

1. Identify bibliographic facts: title, authors, year, journal/source, DOI/URL, article type, field, and language. Leave unknown fields blank or mark "待人工核验".
2. Read in order: title/abstract, introduction/research question, theory/hypotheses, method/data, results/tables/figures, discussion/contribution, limitations.
3. Extract the paper's real structure rather than forcing a generic template. Always distinguish "paper claims", "evidence shows", and "my interpretation".
4. Explain methods and statistics in plain Chinese. Do not merely name the model; explain what it is used to identify and how to read the key coefficients/effects/metrics.
5. Quote and analyze original text. For a single source, include at least 5 short original passages; for multi-source outputs, include at least 2 short original passages per source. Choose passages that show the article's best insight, turning point, key finding, methodological move, or boundary condition. Pair every quote with a concise Chinese analysis. Keep quotes short and do not reproduce long continuous passages. If only title/abstract is available, mark the quotation requirement as unmet because of evidence limits.
6. Map transferable value to innovation and entrepreneurship, technology transfer, platform governance, IP management, research policy, or organizational practice when relevant.
7. Produce Markdown for durable notes, HTML for polished reading/WeChat preview, and `.docx` when requested. Keep the Markdown or HTML source alongside generated documents.
8. Add a verification section listing what was fully read, what was inferred from abstract/title only, and what needs manual checking.

## Output Modes

### Single-Paper Deep Reading

Use for one focal paper. Include:

- bibliographic card;
- one-paragraph executive summary;
- research question and why it matters;
- theory/concepts;
- research design and data;
- method and statistics explained;
- key findings, with evidence;
- contribution and novelty;
- limitations and cautions;
- transferable implications;
- WeChat-ready version if requested.

Use the template in `templates/single_paper_report.md` when the user asks for a formal report.

### Multi-Paper Digest

Use for journal issues, top-journal updates, or a folder of papers. Include:

- journal/issue overview if available;
- article list with English title, Chinese title, authors, DOI, abstract summary;
- each paper's research question, method, key finding, and usefulness rating;
- "值得优先读" shortlist;
- cross-paper themes and comparison table.

Use `templates/multi_paper_digest.md` when the user asks for a digest.

### WeChat Draft

Use when the user wants public sharing. Follow `references/style_guide.md` and apply the writing audit in `references/writing_audit.md` before finalizing.

Avoid clickbait that distorts the paper. A good WeChat draft may be lively, but it must remain faithful to the evidence. Explain academic terms without dumbing them down. Use short sections, concrete examples, and a clear "so what".

### HTML Report

Use when the user wants a polished, visual, browser-readable output or a WeChat preview. Generate a complete single-file `.html` with embedded CSS and no external dependencies. Include structured sections, tables, figure placeholders, captions, caution boxes, evidence boundaries, and manual-check items.

Use `templates/html_article_report.html` for a single-paper report and adapt it for WeChat drafts. Do not invent charts or images; if a figure/table cannot be extracted, add a clear placeholder and explain what should be inserted.

For WeChat publishing, also output `wechat_article_inline.html` when feasible. This version should use mostly inline styles on headings, paragraphs, cards, tables, and emphasis blocks so that copying from the browser into the WeChat editor preserves more formatting after CSS filtering.

For WeChat publishing, default to a copy-paste-ready article file named `wechat_article_copy_ready.html`. It should be based on `wechat_article_inline.html`, avoid complex layouts and wide tables, and place the project public-account image immediately above the following right-aligned, bold signature block:

`编辑丨姓名，机构/身份`

`审核丨姓名，机构/身份`

`校对丨姓名，机构/身份`

`整理丨姓名，机构/身份`

`课题组/公众号名称`

Reserve one podcast placeholder line immediately below the article title and before the lead paragraph:

`播客丨`

In the WeChat copy-ready version, prefix the article title with `学术播客丨`, using the format `学术播客丨标题`.

Immediately below the `播客丨` line, add this sentence:

`欢迎大家来到“学术播客丨常听日新”栏目。`

For the image insertion area, provide a default 2 x 2 table with four clearly labeled placeholders. Keep it simple and copy-paste friendly so the user can replace each cell with an image inside the WeChat editor.

Above `文献概况`, add a short `期刊概况` section. Include journal ratings/rankings where available: SCI/SSCI/CSSCI status, JCR/中科院/other quartiles, UTD/FT50 status, ABS/AJG rating, and the journal's main fields. Because ratings change over time, verify them from official or credible current sources whenever possible. If a rating cannot be confirmed, write `待人工核验` instead of guessing. Bold high-signal prestige tags: UTD, FT50, and ABS/AJG 3/4/4*.

Also generate a thematically matched cover image for the article, saved as `cover_image.png` in the output folder when image generation is available. The cover should match the article's topic and mood, contain no readable text by default, and avoid imitating living artists' exact styles. If the user asks for a living artist style, translate it into a broader non-infringing aesthetic description.

Do not include a fixed `场景拓展` section in the WeChat copy-ready article. Keep a final `思考讨论` block, but make the discussion question expand from the article's topic and evidence rather than from the user's personal research. Near the end of the HTML article, insert the project public-account image as `public_account_qr.png` immediately above the signature block when available. The default source asset is `assets/public_account_qr.png`; if it is missing, copy it from `assets/public_account_qr.png` before final delivery.

## Quality Rules

- Before delivering any public-facing draft, run the internal writing audit in `references/writing_audit.md`: remove predictable LLM boilerplate, neutralize emotional or subjective tone, standardize disciplinary terms, and adjust voice/focus so the research object and evidence stay central.
- Add a visible `原文摘录与剖析` section or weave equivalent quote-analysis blocks into the body. Single-paper, report, article, or non-journal outputs need at least 5 short original passages; multi-paper or issue-tracking outputs need at least 2 short original passages per paper/material. Select excerpts for their explanatory force, not just because they contain keywords.
- Prefer "这篇文章发现..." only when the paper provides evidence; use "作者认为..." for theoretical claims or discussion.
- Do not over-translate technical terms. Keep terms such as fsQCA, robustness check, mediation, moderation, endogeneity, Algorithmic Facial Expression Analysis, FACS, DOI, CRO, CDMO, patent citation in English where relevant.
- Do not summarize only the abstract unless the user explicitly asks. If only abstract is available, say so.
- Do not write vague praise such as "具有重要意义" without saying important to whom and why.
- Do not hide uncertainty. Mark missing author/year/journal/DOI as "待人工核验".
- For statistics, explain direction, magnitude, significance, sample, and boundary conditions when available.
- For charts/tables, describe what the figure/table proves, what it does not prove, and whether it supports the stated conclusion.

## File Outputs

Default output folder:

`outputs/journal_reading/`

Recommended files:

- `article_reading_note.md`
- `article_reading_report.html`
- `wechat_draft.html`
- `wechat_article_inline.html`
- `wechat_article_copy_ready.html`
- `cover_image.png`
- `article_reading_report.docx`
- `wechat_draft.md`
- `paper_comparison.xlsx` when comparing multiple papers

When creating `.docx`, preserve clear headings, tables, and references. If document rendering tools are available, render or inspect the document before final delivery.

On Windows, prefer the local wrapper `scripts/render_docx_qa.py` for Word visual QA instead of calling the cached `render_docx.py` directly. The wrapper auto-discovers `soffice.exe`, sets `SOFFICE_PATH`, and then invokes the Codex document renderer. This avoids failures when LibreOffice is installed outside `PATH`.

## Example Materials

When example materials are provided by the user, use them only as style evidence. Do not copy long passages from examples; extract structure, rhythm, and judgment standards.


