# Find or install Pandoc for EPUB2

[Mermaid source](pandoc-install.mmd) · [Verification skill](../../.cursor/skills/verify-docs2epub-pandoc-cache/SKILL.md)

![Find or install Pandoc for EPUB2](pandoc-install.svg)

PATH and cached executables are immediate reuse paths. A fresh download must pass archive validation and a version probe before it becomes a cache entry. The model shows a single installer and abstracts the individual platform archives.

The chart omits transitions that leave the visible label unchanged. Copy `PandocCache.tla` and `PandocCache.cfg` from the skill and `pandoc-install.view.mjs` from this directory into a scratch directory to regenerate. Use pstack at `5866df557357d005b3c0c9d3da0d9e739b4bdde3` and TLC 1.7.4.

```sh
"$PSTACK_STATECHART" PandocCache.tla --view pandoc-install.view.mjs --out pandoc-install
```
