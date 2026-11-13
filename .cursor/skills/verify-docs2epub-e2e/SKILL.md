---
name: verify-docs2epub-e2e
description: Check the manual loopback e2e runner’s sequence, preserved output check and cleanup.
---

# Verify the installed CLI acceptance script

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`scripts/e2e_cli.py::main` starts a loopback server, validates EPUB2 and EPUB3 file builds and an EPUB3 pipe, checks side-effect-free preview, exercises error and timeout paths against an existing book, verifies its digest and staged-file cleanup, and checks a closed help pipe. The server and temporary outputs are cleaned up when a check fails. The script was added after the PyPI release.

The model bounds one runner execution and represents the preserved-book assertion separately from the other successful gates. The mutant accepts a changed digest. ZIP parsing, threading and subprocess behavior are delegated to the real runner and its fixture.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-e2e
sh scripts/check-cli-state-machine.sh "$dir/Acceptance.tla"
sh scripts/check-cli-state-machine.sh "$dir/Acceptance.tla" "$dir/Acceptance-mutant.cfg"
```

With Pandoc available, run `uv run --locked python scripts/e2e_cli.py .venv/bin/docs2epub`. Run `uv run --locked python "$dir/references/check-e2e-gate.py"` to exercise the digest gate independently with a fake installed command. Removing the digest check from a disposable copy of the runner must let the fake succeed.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
