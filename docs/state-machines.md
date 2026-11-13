# docs2epub state machines

Reviewed GitHub main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`. The package registers one console entrypoint, `docs2epub`, in `pyproject.toml`. `scripts/e2e_cli.py` is the separate local acceptance CLI introduced after the release.

| Subsystem | Source and states | Skills and charts |
| --- | --- | --- |
| CLI preflight | `cli.py::_run` handles help, version, validation, destination selection, and dry run. The release has a smaller flag set and sends progress and results to stdout. | [Dispatch](../.cursor/skills/verify-docs2epub-dispatch/SKILL.md) · [Preview chart](statecharts/preview.md) |
| Discovery | `docusaurus_next.py` fetches the first page, optionally refetches a canonical URL, and selects GitHub tree, GitHub blob, sidebar, linked `llms.txt`, or Next traversal. | [Discovery](../.cursor/skills/verify-docs2epub-discovery/SKILL.md) |
| HTML chapter traversal | `docusaurus_next.py` visits and expands a sidebar queue or follows Next links. It skips unavailable secondary sidebar pages. Both revisions can fetch past the chapter limit and resolve a nested relative Next link against the original directory. | [Crawl](../.cursor/skills/verify-docs2epub-crawl/SKILL.md) · [Chapter limit chart](statecharts/crawl.md) |
| Markdown chapter traversal | `docusaurus_next.py` consumes GitHub and linked-index candidates, tracks redirect cycles, and deduplicates final chapter URLs. Main propagates the configurable page timeout to each fetch. | [Markdown](../.cursor/skills/verify-docs2epub-markdown/SKILL.md) |
| Images | `kindle_images.py` normalizes images and caches successful conversions. EPUB2 uses it on both revisions. Main extends the image pipeline to EPUB3. Failed image references are retried. | [Images](../.cursor/skills/verify-docs2epub-images/SKILL.md) |
| Pandoc installation | `pandoc.py` selects PATH, cache, or a platform archive. Fresh installs validate and probe the staged executable before publishing the cache entry. | [Pandoc cache](../.cursor/skills/verify-docs2epub-pandoc-cache/SKILL.md) · [Install chart](statecharts/pandoc-install.md) |
| Book assembly | `epub.py`, `pandoc_epub2.py`, `book_links.py`, and `kindle_html.py` prepare assets and chapter URLs, normalize anchors, build metadata and navigation, and run the chosen writer. Main directs Pandoc warnings to stderr. | [Assembly](../.cursor/skills/verify-docs2epub-assembly/SKILL.md) |
| Delivery | `cli.py::_convert` stages a completed book before atomic replacement or binary stdout. `main` handles interruption and closed pipes. The release writes directly to the file destination and can overwrite it on a writer failure. | [Delivery](../.cursor/skills/verify-docs2epub-delivery/SKILL.md) · [Delivery chart](statecharts/delivery.md) |
| Package build and release | `pyproject.toml` and `.github/workflows/publish.yml` build a wheel and source archive and gate publishing on a successful tagged build. `.github/workflows/ci.yml` delegates its test lifecycle to uv and pytest. | [Release](../.cursor/skills/verify-docs2epub-release/SKILL.md) |
| Installed CLI acceptance | `scripts/e2e_cli.py` starts a local server, exercises both output formats, checks binary stdout and dry run, then checks recovery and server cleanup. | [Acceptance](../.cursor/skills/verify-docs2epub-e2e/SKILL.md) |

`model.py` defines the chapter record. `__init__.py` exposes version metadata. Their values feed the modeled subsystems.

The models check bounded state and documented properties. Source replays use deterministic HTML and HTTP doubles, temporary output paths, and a loopback server for the installed CLI. Pandoc, EbookLib, requests, Pillow, CairoSVG, and OS primitives enter the models through their observed interfaces and outcomes.
