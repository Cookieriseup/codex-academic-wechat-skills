---
name: journal-tracking
description: Use when the user provides two or more academic materials, articles, PDFs, DOI links, journal issue pages, online-first lists, screenshots, abstracts, or paper folders and wants a Chinese journal-tracking digest, WeChat public-account article, issue roundup, or comparative new-paper scan. 中文名：期刊追踪。
---

# Journal Tracking / 期刊追踪

## Goal

Turn two or more academic materials into a structured Chinese "期刊追踪" output for:

- journal issue tracking;
- online-first new-paper tracking;
- top-journal roundup posts;
- WeChat public-account sharing;
- seminar or group-reading shortlist.

Use this skill only for 2+ materials. For a single paper, use `journal-reading`.

## Default Trigger

In journal/public-account projects, when the user provides two or more PDFs, DOI links, URLs, screenshots, article titles, abstracts, or a folder/list of papers, default to:

`Use $journal-tracking to produce a WeChat-ready journal tracking digest.`

The default title format is:

`期刊追踪丨标题`

Reserve one podcast placeholder line immediately below the title:

`播客丨`

Immediately below the podcast line, add:

`欢迎大家来到“学术播客丨期刊追踪”栏目。`

## Source Pattern

Follow the style pattern of journal issue roundup posts, especially examples organized around a journal volume/issue such as `Research Policy: Vol 52, Issue 10, 2023`:

- start with journal/issue context;
- include issue metadata and journal ranking/field notes when available;
- present a clean table of contents or "本期速览";
- add a readable `期刊介绍` block at the end of `01 本期速览`, explaining the journal's positioning, fields, ranking/status, and why this issue/batch matters;
- use numbered article cards;
- each card includes English title, Chinese title, authors, citation/source, DOI/URL, Abstract, 中文摘要, keywords when available, and "为什么值得读";
- keep article cards concise enough for phone reading;
- do not over-comment on papers that have only titles/abstracts.

## Workflow

1. Identify input scope: journal name, volume/issue, online-first batch, topic set, or user-provided folder/list.
2. Build an inventory: item id, title, Chinese title, authors, year, journal/source, volume/issue/pages/article number, DOI/URL, abstract, keywords, evidence status.
3. Verify and preserve evidence boundaries: full-text read, abstract-only, title-only, inaccessible, duplicate, or needs manual check.
4. Group papers by theme if useful. Prefer 3-5 meaningful topic groups over a flat list when the issue contains many papers.
5. Quote and analyze original text. Include at least 2 short original passages for each paper/material when full text or abstract text is available. Choose excerpts that capture the paper's best insight, point of tension, key finding, method, or boundary condition. Pair every quote with concise Chinese analysis. Keep excerpts short and mark `无法满足原文引用数量` when only title/metadata is available.
6. Draft a WeChat-ready article with the structure in `references/style_guide.md`.
7. Apply the internal writing-audit principles inherited from `journal-reading`: remove predictable LLM boilerplate, neutralize exaggerated tone, keep terms precise, and distinguish paper claims from interpretation.
8. Output HTML first, Markdown second when useful. For WeChat, use mostly inline styles and avoid complex layouts.

## Default Outputs

Recommended output folder:

`outputs/journal_tracking/<slug>/`

Recommended files:

- `journal_tracking_inventory.xlsx` when feasible;
- `journal_tracking_report.md`;
- `journal_tracking_report.html`;
- `wechat_tracking_copy_ready.html`;
- `wechat_tracking_inline.html`;
- `tracking_metadata.json`;
- copied `public_account_qr.png` when available.

## WeChat Footer

At the end of the WeChat-ready HTML, place the project public-account image `public_account_qr.png` immediately above this right-aligned, bold signature block:

`编辑丨姓名，机构/身份`

`审核丨姓名，机构/身份`

`校对丨姓名，机构/身份`

`整理丨姓名，机构/身份`

`课题组/公众号名称`

Use `assets/public_account_qr.png` as the default source asset. If missing, try `assets/public_account_qr.png`.

## Quality Rules

- Do not invent abstracts, DOI, journal rankings, authors, or issue metadata.
- Add quote-analysis blocks for every paper/material: at least 2 short original passages per paper/material, selected because they show the paper's highlight, key claim, method, finding, or limitation. Do not paste long continuous passages. If the source is abstract-only, quote from the abstract and label the evidence boundary.
- If only a title is available, mark the item as `题名可见，摘要待核验`.
- If only an abstract is available, do not imply that full text was read.
- Keep English technical terms where they are journal-specific or methodological.
- For each paper card, include at least one concrete reason why it belongs in the tracking digest.
- Avoid single-theme monotony. A tracking article should help readers scan, compare, and decide what to read next.
- When journal rankings change over time, mark uncertain rankings as `待人工核验`.


