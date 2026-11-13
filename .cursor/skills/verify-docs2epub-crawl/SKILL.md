---
name: verify-docs2epub-crawl
description: Check sidebar queue and fallback Next navigation when changing crawl deduplication, skips or page limits.
---

# Verify chapter traversal and page limits

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`src/docs2epub/docusaurus_next.py::iter_docusaurus_next` reads the start page, optionally refetches a same-host canonical URL, then chooses GitHub Markdown, linked `llms.txt` without a sidebar, sidebar traversal, or Next navigation. Sidebar traversal expands an ordered queue with in-scope content links, tracks discovered and visited canonical keys, and skips unavailable secondary chapters. The Next path obtains the next URL and fetches it before looping back to check the chapter cap. Both revisions can request a second page with a one-page cap, and a failed fetch can turn an otherwise complete one-page book into an error.

The model bounds two page identities, limits of one or two, and sidebar or Next paths. It checks the chapter cap and the stronger rule that the crawl stops fetching once it is met. The current config must fail the stronger rule. The alternative moves the cap check before the next request. Canonicalization, discovery heuristics and redirect handling are separate from this bounded traversal.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-crawl
sh scripts/check-cli-state-machine.sh "$dir/Crawl.tla"
sh scripts/check-cli-state-machine.sh "$dir/Crawl.tla" "$dir/Crawl-check-first.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_docusaurus_next.py tests/test_sidebar_scrape.py`. Then run `uv run --locked python "$dir/references/replay-crawl.py"`. It supplies local HTML for a single accepted chapter and makes the second Next page return HTTP 503. Both source revisions request that page and propagate the error. Add a limit check before the Next fetch in a disposable tree and use `DOCS2EPUB_EXPECT_STOP=1` to check the alternative.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.

## Relative Next links

The fallback loop calls `_extract_next_url` with the original resolution base on each iteration, even after navigating into another directory. Both revisions can fetch the wrong page when a later Next link is relative. `NextBase.tla` bounds one absolute hop followed by one relative hop, with no explicit base override. Its baseline must fail `NextResolvesAgainstCurrentPage`. The alternate config resolves the second link against the currently read page.

```sh
sh scripts/check-cli-state-machine.sh "$dir/NextBase.tla"
sh scripts/check-cli-state-machine.sh "$dir/NextBase.tla" "$dir/NextBase-current-page.cfg"
uv run --locked python "$dir/references/replay-next-base.py"
```

In a disposable checkout, pass `options.base_url or current_url` in the fallback loop, then replay with `DOCS2EPUB_CURRENT_NEXT_BASE=1`.
