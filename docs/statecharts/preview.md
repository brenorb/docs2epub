# Preview or start an EPUB conversion

[Mermaid source](preview.mmd) · [Verification skill](../../.cursor/skills/verify-docs2epub-dispatch/SKILL.md)

![Preview or start an EPUB conversion](preview.svg)

Help, version, usage errors, and dry run all stop before crawling. A valid conversion proceeds to scraping. The model treats arguments as validated invocation classes and excludes token parsing internals.

The chart omits transitions that leave the visible label unchanged. Copy `Dispatch.tla` and `Dispatch.cfg` from the skill and `preview.view.mjs` from this directory into a scratch directory to regenerate. Use pstack at `5866df557357d005b3c0c9d3da0d9e739b4bdde3` and TLC 1.7.4.

```sh
"$PSTACK_STATECHART" Dispatch.tla --view preview.view.mjs --out preview
```
