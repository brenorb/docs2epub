---
name: verify-docs2epub-images
description: Check image eligibility, processing and per-book cache behavior for EPUB2 and EPUB3.
---

# Verify image reuse and failed-download retries

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`src/docs2epub/kindle_images.py::KindleImageProcessor.rewrite` resolves eligible image URLs, downloads and converts SVG or raster assets, keeps GIF bytes, and remembers successful paths across chapters. The cache stores `None` on HTTP or conversion failure, then treats that value as a miss on later references. An image that keeps failing may be downloaded repeatedly. Retrying can recover a transient failure. Current EPUB2 and EPUB3 use this processor when images are enabled. The PyPI release applies it only to EPUB2.

The model bounds two references to one eligible URL and two representative conversion outcomes. The known-failure config tests at-most-one request and shows a retry. The alternative remembers failures. The mutant disables reuse of a successful result. Individual codec behavior and provider failures are modeled as outcomes.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-images
sh scripts/check-cli-state-machine.sh "$dir/Images.tla"
sh scripts/check-cli-state-machine.sh "$dir/Images.tla" "$dir/Images-known.cfg"
sh scripts/check-cli-state-machine.sh "$dir/Images.tla" "$dir/Images-remember-failure.cfg"
sh scripts/check-cli-state-machine.sh "$dir/Images.tla" "$dir/Images-mutant.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_kindle_images.py tests/test_smoke.py` and `uv run --locked python "$dir/references/replay-images.py"`. The fixture checks repeated 404s and recovery when the second request succeeds. To test the successful cache in a disposable tree, force `cached = None` in `rewrite` and rerun the cache test.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
