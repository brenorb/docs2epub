---
name: verify-docs2epub-delivery
description: Check staged EPUB publication, preserved destination bytes and file versus stdout routing.
---

# Verify EPUB file replacement and binary stdout

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`src/docs2epub/cli.py::_convert` fetches chapters before creating a staging directory, passes the staged path to the selected writer, reads the completed size, and either streams binary EPUB bytes or atomically replaces the file with `os.replace`. For existing files it copies mode bits before replacement. `main` maps interrupts to 130 and closed output pipes to successful exit. The release sends the real destination directly to both writers and has only the file path.

The model bounds one conversion with one file or binary destination, and one failure or interrupt before commitment. The legacy config represents the released direct-write path and must expose a destination change before commit. The pipe model allows a failure during streaming. Bytes already written to a pipe cannot be rolled back. File metadata, cleanup errors, parent directory creation, concurrent file replacement, and external converter behavior are outside the checked invariant.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-delivery
sh scripts/check-cli-state-machine.sh "$dir/Delivery.tla"
sh scripts/check-cli-state-machine.sh "$dir/Delivery.tla" "$dir/Delivery-legacy.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_cli_contract.py -k 'failed_conversion or ctrl_c or stdout_destination'`. The tests inject writers that create partial bytes and fail. Replay the released path with the fixture in `references/replay-delivery.py` in a disposable checkout and `DOCS2EPUB_LEGACY=1` set. It demonstrates destination overwrite on an EPUB2 writer failure. Main must preserve the same bytes.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
