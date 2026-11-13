---
name: verify-docs2epub-dispatch
description: Check CLI information commands, argument validation and dry-run dispatch before a conversion can begin.
---

# Verify CLI preflight and dry-run dispatch

Reviewed main at `8b7b3687f6c406f2792f2ba33636929323fd5428` and the PyPI release `v0.1.15` at `aa036fd73feb298d380a669b675c99a613acac6c`.

`src/docs2epub/cli.py::_run` handles bare invocation and information flags before parsing conversion options, and scans only before the literal `--` boundary. Explicit URL and destination flags take precedence. Validation checks required arguments, HTTP(S) URL and port, positive page count, bounded finite durations, and incompatible binary stdout choices. `_convert` returns the plan before scraping or preparing files. The release requires a URL and destination, uses the default argparse option matching and has no dry run, JSON summary, binary stdout, or configurable request timeout.

The model represents eight invocation classes and ends when conversion can start. Its invariant keeps preview, usage errors and information commands free of conversion work. The mutant permits conversion outside preflight. It excludes argparse token normalization, exact diagnostics, and operating-system stream behavior.

Use Java 11 or later and set `TLA2TOOLS` to the absolute path of the official [TLC 1.7.4 JAR](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

```sh
dir=.cursor/skills/verify-docs2epub-dispatch
sh scripts/check-cli-state-machine.sh "$dir/Dispatch.tla"
sh scripts/check-cli-state-machine.sh "$dir/Dispatch.tla" "$dir/Dispatch-mutant.cfg"
```

Run `uv run --locked --extra dev pytest -q tests/test_cli_contract.py`. To verify the dry-run guard in a disposable source tree, replace `if args.dry_run:` in `_convert` with `if False:`. The existing dry-run test must detect that the crawler was called. Restore and rerun.

Use pstack’s `/statechart` to inspect shortest paths. Advance the reviewed revision after checking the model against the changed source and replaying the fixtures.
