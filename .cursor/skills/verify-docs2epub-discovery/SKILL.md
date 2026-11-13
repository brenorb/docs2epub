---
name: verify-docs2epub-discovery
description: Check canonical refetch, preservation of crawl scope and precedence among documentation discovery methods.
---

# Verify discovery precedence and canonical refetch

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

In `src/docs2epub/docusaurus_next.py::iter_docusaurus_next`, canonical refetch is allowed when the initial page declares a changed same-host URL and the caller supplied no base override. Refetch changes the request and resolution base, while the original URL continues to supply the scope for sidebar, content, and linked `llms.txt` discovery. A GitHub tree wins over a blob, and a sidebar suppresses the `llms.txt` branch. With no recognized index, the crawler follows Next links.

The model exhausts all subsets of four strategy hints and four representative canonical outcomes. It summarizes HTML parsing and treats the canonical fetch as successful. It checks that refetch preserves scope and that a recognized sidebar suppresses the linked index.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-discovery
sh scripts/check-cli-state-machine.sh "$dir/Discovery.tla"
sh scripts/check-cli-state-machine.sh "$dir/Discovery.tla" "$dir/Discovery-mutant.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_sidebar_scrape.py`. In a disposable checkout, change the sidebar call to pass `start_url=url` in place of `start_url=crawl_scope_url`. The original-scope regression must fail. Restore and rerun.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
