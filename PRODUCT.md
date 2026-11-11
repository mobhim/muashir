# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: static HTML/CSS/JS with no build step. The data pipeline is Python and already writes its outputs to disk, so the site reads one generated JSON file; it opens from a folder and deploys to GitHub Pages as-is, matching the owner's earlier sites. Node.js is not installed on the owner's machine.

## Users

Two audiences, equal weight (confirmed by the owner):

- Individual investors in the Saudi market who read quarterly earnings announcements and want to know whether a "good report" is still a reason to buy after the news is out.
- Recruiters and academics evaluating the owner, a student in AI and data analysis, who want to see the question, the method, the result and the code.

## Product Purpose

Muashir (مؤشّر) presents an event study of quarterly earnings announcements on the Saudi exchange and lets the visitor explore it. Success for a visitor: they leave able to state the finding in one sentence, they trust how it was measured, and they have looked up at least one company themselves. The owner confirmed the shape as "story first, then a tool".

## Positioning

Muashir scores each earnings announcement from 0 to 100 using only information available on the day, then tests that score against what the stock did next, and publishes the answer even where it is "no". The whole chain from raw download to chart is reproducible from the repository.

## Operating Context

- Source: Yahoo Finance prices, announcement dates, reported and estimated EPS.
- Pipeline: `python -m muashir.pipeline` rebuilds the database, the report, the Power BI tables and the site data.
- Related artifacts: `reports/REPORT.md`, `powerbi/Muashir.pbip`.
- Language: Arabic, right-to-left. Numbers in Western digits.

## Capabilities and Constraints

- 1,159 announcements, 37 companies, 44 reporting seasons, 2016 to 2026.
- Seven score components; two are proxies (analyst surprise in place of revenue growth, market beta in place of geopolitical independence).
- Market benchmark is an equal-weighted average of the other sample stocks, because index history is not available from the source.
- Announcement dates are accurate to about one session.
- Not investment advice; Yahoo data is for personal use.
- Undecided: public domain or hosting account; whether real company logos will be used (none are in the project).

## Brand Commitments

- Name: مؤشّر (Muashir).
- The owner rejected a calm, reading-first design (green wall-calendar direction) on 2026-11-11 and set the bar as their own Cerebra and Sila sites: cinematic, dark, moving from the first frame, feature-rich, with very little text. That level is binding for this site.
- Black and gold with cream text, as in the first Muashir site.
- Voice: one or two short lines per section in plain Saudi Arabic; the answer before the method; limits stated openly but collapsed.

## Evidence on Hand

- `reports/results.json`: every statistic shown on the site.
- `data/muashir.db` and `powerbi/data/*.csv`: per-announcement scores, abnormal returns and daily paths.
- `reports/figures/*.png`: static versions of the four charts.
- No testimonials, users, press or logo files exist; none may be invented.

## Product Principles

1. The answer comes first, including when it is negative.
2. Every number on the page is traceable to the pipeline output.
3. Limits are part of the result, not a footnote.
4. The visitor can check a claim themselves in the explorer.

## Accessibility & Inclusion

Arabic RTL throughout; charts must be readable without relying on colour alone and must have text equivalents of their key values.
