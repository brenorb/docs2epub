---
name: verify-docs2epub-markdown
description: Check Markdown redirect cycles, final-target deduplication and chapter publication in the GitHub and llms.txt paths.
---

# Verify Markdown redirect and chapter deduplication

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`consume_markdown_url` inside `src/docs2epub/docusaurus_next.py::iter_docusaurus_next` tracks canonical URLs within each Markdown redirect chain, skips a missing page or a cycle, and deduplicates successful final URLs across chains before adding chapters. The GitHub tree, GitHub blob and linked `llms.txt` routes call this machinery. The tree and index check the chapter count between candidates.

The model uses two sources which can converge on one final URL, return missing, or cycle. Its invariant checks that the converging routes yield one chapter. It abstracts Markdown conversion, network status outside 404/410, and longer chains.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-markdown
sh scripts/check-cli-state-machine.sh "$dir/Markdown.tla"
sh scripts/check-cli-state-machine.sh "$dir/Markdown.tla" "$dir/Markdown-mutant.cfg"
```

Run `uv run --locked python "$dir/references/replay-markdown.py"`. The fixture drives two convergent local redirects and a self-cycle through a linked index. In a disposable checkout bypass `if final_key in markdown_seen:` to catch duplicate publication.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
