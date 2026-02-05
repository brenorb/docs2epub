# docs2epub AGENTS

This file documents local conventions for working on `docs2epub`.

**Focus**
- Keep the scraper generalistic across doc-site frontends (GitBook, Docusaurus, similar).
- Prefer resilient HTML heuristics over site-specific hacks.
- Fail gracefully when content is missing; surface actionable errors.

**Development Workflow**
- Use TDD for bug fixes and new behaviors. Add a failing test first.
- Prefer unit tests with `monkeypatch` and deterministic HTML fixtures.
- Keep tests fast and offline. Only do real network checks for manual validation.
- Run tests with `uv run pytest -q`.

**Scraping Heuristics**
- Primary crawl: sidebar/index extraction.
- Expand index/category pages by collecting in-page content links.
- Fallback crawl: “Next” navigation when no sidebar is found.
- Normalize URLs: strip fragments and queries; lower-case scheme/host.
- Filter non-doc links by extension; avoid cross-origin URLs by default.
- Resolve relative URLs against the page URL, not the site root.

**Code Layout**
- Core crawler logic: `src/docs2epub/docusaurus_next.py`.
- EPUB generation: `src/docs2epub/epub.py` and `src/docs2epub/pandoc_epub2.py`.
- HTML cleanup: `src/docs2epub/kindle_html.py`.
- Tests live in `tests/`.

**Release Discipline**
- Bump version in `pyproject.toml` for user-visible changes.
- Run `uv lock` after bumping the version.
- Build artifacts with `uv build` before publishing.
- Publish with `uv publish` when explicitly requested.
- Do not commit generated EPUBs or other artifacts.

**Validation**
- Quick manual checks (optional):
  - `uvx --from . docs2epub https://midl.gitbook.io/midl out.epub`
  - `uvx --from . docs2epub https://tutorial.docusaurus.io/docs/intro out.epub`
- Clean up any generated files after validation.
