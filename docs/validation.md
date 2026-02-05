# Validation Notes

This file records manual validation runs and known behaviors for target sites.

## Pyodide (Sphinx)
- URL: `https://pyodide.org/`
- Canonical: `https://pyodide.org/en/stable/index.html`
- Behavior: sidebar links resolve under `/en/stable/`.
- Non-content pages (e.g., `console.html`) have no `<article>`; those are skipped.
- Local validation (after fixes): `uvx --from . docs2epub https://pyodide.org/ out.epub` scraped 52 pages.

## GitBook (MIDL)
- URL: `https://midl.gitbook.io/midl`
- Behavior: sidebar/table-of-contents scrape works.
- Local validation: `uvx --from . docs2epub https://midl.gitbook.io/midl out.epub` scraped 11 pages.

## Docusaurus (Tutorial)
- URL: `https://tutorial.docusaurus.io/docs/intro`
- Behavior: sidebar + index expansion works.
- Local validation: `uvx --from . docs2epub https://tutorial.docusaurus.io/docs/intro out.epub` scraped 11 pages.

## Trunk-Based Development
- URL: `https://trunkbaseddevelopment.com/`
- Behavior: sidebar crawl works; lots of images missing by default.
- Validation: `uvx docs2epub https://trunkbaseddevelopment.com/ out.epub` scraped 28 pages.

## Social Skills Wisdom
- URL: `https://socialskillswisdom.com/`
- Behavior: single-page scrape (no sidebar detected).
- Validation: `uvx docs2epub https://socialskillswisdom.com/ out.epub` scraped 1 page.

## Book of Pook
- URL: `https://bookofpook.com/`
- Behavior: single-page scrape (no sidebar detected).
- Validation: `uvx docs2epub https://bookofpook.com/ out.epub` scraped 1 page.

## Basecamp Getting Real
- URL: `https://basecamp.com/gettingreal`
- Behavior: sidebar crawl works.
- Validation: `uvx docs2epub https://basecamp.com/gettingreal out.epub` scraped 92 pages.

## Basecamp Shape Up
- URL: `https://basecamp.com/shapeup`
- Behavior: sidebar crawl works.
- Validation: `uvx docs2epub https://basecamp.com/shapeup out.epub` scraped 24 pages.

## RLHF Book
- URL: `https://rlhfbook.com/`
- Behavior: single-page scrape (no `<article>`; body fallback used).
- Validation: `uvx docs2epub https://rlhfbook.com/ out.epub` scraped 1 page.

## UltraScale Playbook (Hugging Face Space)
- URL: `https://huggingface.co/spaces/nanotron/ultrascale-playbook`
- Behavior: single-page scrape.
- Validation: `uvx docs2epub https://huggingface.co/spaces/nanotron/ultrascale-playbook out.epub` scraped 1 page.

## Python for Data Analysis (Wes McKinney)
- URL: `https://wesmckinney.com/book/`
- Behavior: sidebar crawl works; many images missing by default.
- Validation: `uvx docs2epub https://wesmckinney.com/book/ out.epub` scraped 18 pages.

## Mastering Bitcoin (GitHub)
- URL: `https://github.com/bitcoinbook/bitcoinbook/blob/develop/BOOK.md`
- Behavior: single-page scrape (GitHub HTML page).
- Validation: `uvx docs2epub https://github.com/bitcoinbook/bitcoinbook/blob/develop/BOOK.md out.epub` scraped 1 page.
