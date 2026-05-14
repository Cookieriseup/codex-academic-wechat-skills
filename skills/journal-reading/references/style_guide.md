# Style Guide

## Two Supported Styles

### 1. Deep WeChat Article

Observed pattern from the case materials:

- headline is vivid and problem-driven;
- opening gives a concrete scenario or surprising tension;
- the paper is introduced early with journal/source and core concept;
- technical terms are kept in English and explained in Chinese;
- sections use short, direct questions or claims;
- methods and indicators are translated into everyday logic;
- examples are used to make the mechanism memorable;
- conclusion returns to practical implications, not just academic contribution.

Use this structure:

1. Title: vivid but faithful.
2. Lead: 100-200 Chinese characters, stating the puzzle and the paper's core answer.
3. "这篇论文研究了什么": paper, journal, authors if known, research question.
4. "它为什么重要": real-world or research-field problem.
5. "作者怎么研究": data, sample, design, method, measures.
6. "最关键的发现": 3-5 findings, each with evidence.
7. "原文摘录与剖析": at least 5 short original passages for a single paper/source, each followed by analysis.
8. "研究局限": limitations, boundary conditions, causal caution.
9. "可以迁移到哪里": innovation/entrepreneurship/technology transfer/IP/AI governance/management practice.
10. Closing: one sharp takeaway and optional discussion question.

For single-paper, report, article, or other non-journal source outputs, include at least 5 short original excerpts. Choose passages that reveal the source's best insight, turning point, key claim, method, finding, or boundary condition. Each excerpt must be followed by concise analysis that explains why it is a point of emphasis. Do not paste long continuous passages.

For WeChat handoff, produce an additional `wechat_article_inline.html` when possible. It should be copy-paste oriented: use inline styles rather than relying on a global `<style>` block, avoid complex layouts, keep cards as simple bordered `div` blocks, avoid wide tables on mobile, and keep local-image placeholders clearly marked for manual replacement.

For the final WeChat handoff, also produce `wechat_article_copy_ready.html`. It must place the project public-account image immediately above this right-aligned, bold signature block:

编辑丨姓名，机构/身份

审核丨姓名，机构/身份

校对丨姓名，机构/身份

整理丨姓名，机构/身份

课题组/公众号名称

It must also reserve one podcast placeholder line immediately below the article title:

播客丨

The WeChat copy-ready article title should use the format `学术播客丨标题`. Immediately below the `播客丨` line, add:

欢迎大家来到“学术播客丨常听日新”栏目。

Use a simple 2 x 2 image placeholder table by default. Suggested cells: 原文关键图表, 机制示意图, 主题延展图, 封面/配图备用. The table is for manual image replacement in the WeChat editor, so keep styling simple and inline-friendly.

Before `文献概况`, add `期刊概况`: journal rating/ranking and field information. Cover SCI/SSCI/CSSCI status, JCR/中科院/other quartiles, UTD/FT50, ABS/AJG, and main fields when available. Verify current ratings where possible; otherwise mark `待人工核验`. Bold UTD, FT50, and ABS/AJG 3/4/4* labels.

Generate or provide a topic-matched cover image as `cover_image.png` when image generation is available. Use broad aesthetic descriptions rather than imitating specific living artists.

Do not include a fixed `场景拓展` section. Use a final `思考讨论` block instead, with a question that expands from the paper's topic, evidence, or theoretical tension. Do not frame the question around the user's personal research. Insert the project public-account image as `public_account_qr.png` immediately above the signature block when available; use `assets/public_account_qr.png` as the default source asset.

### 2. Journal-Issue or Multi-Paper Digest

Observed pattern from the case materials:

- starts with journal introduction and issue information;
- lists table of contents bilingually;
- each article has English title, Chinese title, authors, citation/DOI when available;
- abstract is translated or condensed;
- practical reading value is briefly marked.

Use this structure:

1. Journal and issue overview.
2. "本期目录": English title + Chinese title.
3. Per-paper card:
   - English title;
   - Chinese title;
   - authors;
   - journal/year/volume/issue/pages/DOI;
   - abstract in Chinese;
   - research question;
   - method/data;
   - key finding;
   - 2 short original excerpts with analysis;
   - why it matters;
   - recommended audience.
4. "优先阅读清单": 3-5 papers ranked by relevance.
5. Cross-paper themes.

For multi-paper digests, quote at least 2 short original passages per paper/material when abstract or full text is available. If only titles or metadata are available, explicitly mark the evidence boundary and do not fabricate quotes.

## Tone

Write in polished Chinese. It can be lively for WeChat, but not sensational beyond the paper's evidence. Avoid translationese, empty academic slogans, and generic summary paragraphs.

Before final delivery, apply `writing_audit.md` as an internal cleanup pass. The final article should not contain audit labels or process notes.

Good sentence habits:

- Explain mechanisms: "这不是因为A本身神奇，而是因为A改变了B..."
- Separate claim and evidence: "作者的证据来自..." / "这意味着..." / "但不能推出..."
- Use English terms naturally: "这里的 moderation 不是简单的'调节一下'，而是..."

Bad habits:

- Only paraphrasing the abstract.
- Turning every result into "显著促进".
- Ignoring sample, method, and boundary conditions.
- Writing public-account prose that contradicts or exaggerates the paper.


