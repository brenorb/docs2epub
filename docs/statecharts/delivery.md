# Deliver a documentation EPUB

[Mermaid source](delivery.mmd) · [Verification skill](../../.cursor/skills/verify-docs2epub-delivery/SKILL.md)

![Deliver a documentation EPUB](delivery.svg)

The CLI writes to temporary storage. A complete book is committed to a file or copied to redirected stdout. The bounded check preserves an existing file before commit. It treats writer errors, interrupted streams, and atomic replacement as outcomes.

The chart omits transitions that leave the visible label unchanged. Copy `Delivery.tla` and `Delivery.cfg` from the skill and `delivery.view.mjs` from this directory into a scratch directory to regenerate. Use pstack at `5866df557357d005b3c0c9d3da0d9e739b4bdde3` and TLC 1.7.4.

```sh
"$PSTACK_STATECHART" Delivery.tla --view delivery.view.mjs --out delivery
```
