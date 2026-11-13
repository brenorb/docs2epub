---
name: verify-docs2epub-assembly
description: Check chapter registration, local link rewriting and writer failure before CLI delivery.
---

# Verify book assembly, link rewriting and writer outcomes

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`build_epub` in `epub.py` and `build_epub2_with_pandoc` in `pandoc_epub2.py` materialize the chapters and map canonical URLs before rewriting links with `book_links.py`. EPUB2 cleans HTML, writes temporary inputs and invokes Pandoc with a resource path. Nonzero child exit prevents a result. Main prints child diagnostics to stderr. The release prints successful warnings to stdout. EPUB3 adds image items, metadata, chapter items, navigation and spine before calling EbookLib. Main preprocesses images; the release does not. Kindle HTML cleaning normalizes tags and deduplicates IDs before checking local fragment links.

The model bounds one book with two chapters and one link between them. The invariant checks that an emitted link to a collected chapter was rewritten before writing. It abstracts format-specific filenames and delegates actual archive generation and Pandoc outcomes to source fixtures. It does not guarantee the final identifier survives Pandoc's chapter splitting.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-assembly
sh scripts/check-cli-state-machine.sh "$dir/Assembly.tla"
sh scripts/check-cli-state-machine.sh "$dir/Assembly.tla" "$dir/Assembly-mutant.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_pandoc_epub2.py tests/test_smoke.py`. In a disposable checkout, pass an empty chapter map to `rewrite_internal_book_links` in each writer. The internal-link fixtures must fail. Restore both calls.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.

## Kindle chapter anchors

`kindle_html.py::clean_html_for_kindle_epub2` processes IDs in document order, records each emitted ID, then removes fragment links whose targets are absent. `Anchors.tla` checks uniqueness and retained-link resolution on up to three representative nonblank IDs, including a suffix already in use. It abstracts whitespace normalization and Pandoc’s later transformation. The mutant leaves duplicate IDs as written and must fail `AnchorsUnique`.

```sh
sh scripts/check-cli-state-machine.sh "$dir/Anchors.tla"
sh scripts/check-cli-state-machine.sh "$dir/Anchors.tla" "$dir/Anchors-mutant.cfg"
uv run --locked --extra dev pytest -q tests/test_smoke.py -k deduplicates_ids
```

In a disposable checkout, bypass duplicate renaming and rerun the fixture to catch the repeated ID.
