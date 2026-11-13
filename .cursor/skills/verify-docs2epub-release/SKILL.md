---
name: verify-docs2epub-release
description: Check docs2epub’s release build ordering and wheel console entrypoint.
---

# Verify tagged wheel and source distribution gate

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`.github/workflows/publish.yml` starts on version tags and runs checkout, uv setup and Python setup before `uv build` and `uv publish`. The separate CI workflow installs development dependencies and runs pytest on main and pull requests. `pyproject.toml` uses Hatchling and exposes `docs2epub.cli:main` as the console script.

The model bounds one run, allowing build failure or success. The negative config attempts publication before the build finishes. It models an attempted publish and leaves registry behavior and retries outside the invariant.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-release
sh scripts/check-cli-state-machine.sh "$dir/Release.tla"
sh scripts/check-cli-state-machine.sh "$dir/Release.tla" "$dir/Release-mutant.cfg"
```

Run `uv run --locked python "$dir/references/check-wheel.py"`. The fixture checks tag and step order and builds the source and wheel locally into a temporary directory. Change the console entrypoint in a disposable copy and the wheel assertion must fail.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
