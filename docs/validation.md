# Validation Notes

This file records manual validation runs and known behaviors for target sites.

## Pyodide (Sphinx)
- URL: `https://pyodide.org/`
- Canonical: `https://pyodide.org/en/stable/index.html`
- Behavior: sidebar links resolve under `/en/stable/`.
- Non-content pages (e.g., `console.html`) have no `<article>`; those are skipped.
- Local validation (after fixes): `uvx --from . docs2epub https://pyodide.org/ out.epub` scraped 50 pages.

## GitBook (MIDL)
- URL: `https://midl.gitbook.io/midl`
- Behavior: sidebar/table-of-contents scrape works.
- Local validation: `uvx --from . docs2epub https://midl.gitbook.io/midl out.epub` scraped 11 pages.

## Docusaurus (Tutorial)
- URL: `https://tutorial.docusaurus.io/docs/intro`
- Behavior: sidebar + index expansion works.
- Local validation: `uvx --from . docs2epub https://tutorial.docusaurus.io/docs/intro out.epub` scraped 11 pages.
