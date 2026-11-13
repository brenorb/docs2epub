---
name: verify-docs2epub-pandoc-cache
description: Check executable selection and cache publication after download, checksum validation and a version probe.
---

# Verify automatic Pandoc installation

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`src/docs2epub/pandoc.py::ensure_pandoc` checks PATH, resolves the supported platform, reuses an executable cache entry, or downloads into a temporary directory. On a fresh install it verifies the checksum, copies the executable member, probes `--version`, and atomically replaces the cache file. Both revisions use this sequence.

The model bounds one installation attempt with a failed download or check, failed probe, or successful publication. Existing PATH and cache entries use a separate reuse path. The model abstracts platform mapping, extraction, multiple installers, and filesystem errors. Only fresh cache publication has the verification invariant.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-pandoc-cache
sh scripts/check-cli-state-machine.sh "$dir/PandocCache.tla"
sh scripts/check-cli-state-machine.sh "$dir/PandocCache.tla" "$dir/PandocCache-mutant.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_pandoc.py`. The fixture `uv run --locked python "$dir/references/replay-pandoc.py"` verifies that a failed version probe leaves no cached binary. Comment out the probe in a disposable checkout and rerun to catch the bypass.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
