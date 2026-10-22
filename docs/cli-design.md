# CLI behavior and design decisions

The interface follows the applicable [Command Line Interface Guidelines](https://clig.dev/).

## Discovery and parsing

`docs2epub` without arguments prints a concise introduction. `-h` / `--help`
prints complete help, examples, and documentation/support links, including
when another option is invalid. After a literal `--`, tokens are positional
values. `--version` and Python's `docs2epub.__version__` identify the installed
distribution. Long flags do not abbreviate. The original positional form and
`--out` remain available alongside `-o` / `--output`.

## Results and diagnostics

Human output is concise plain text with no ANSI color or animation, so it also
works with `NO_COLOR`, `TERM=dumb`, redirection, and CI logs. Progress and Pandoc
warnings use stderr. `--quiet` hides progress and keeps the result and warnings.
`--json` produces one structured summary on stdout; scripts should select it
explicitly rather than parse the human text. For a binary EPUB stream, use `-`
as the destination and redirect stdout. Binary output to a TTY is refused.

Success and informational help/version return 0. Usage errors return 2;
conversion, network, and filesystem errors return 1 with a concise explanation.
`Ctrl-C` returns 130 without a traceback. An output pipe closed by a downstream
consumer terminates cleanly. The tool never asks interactive questions, so
automation needs no `--no-input` switch.

## Validation, network, and recovery

URLs, page counts, delays, and request timeouts are checked before scraping.
`--timeout` controls page request timeouts (default 30 seconds); image and
Pandoc installation requests retain their existing bounded timeouts.
Both page timeouts and inter-page delays are limited to 86400 seconds to avoid
platform timer overflows.
`--dry-run` previews source, destination, format, and potential Pandoc download
without network calls or file writes. HTTP proxy environment variables are
handled by Requests. No credentials or telemetry options are added.

Conversions stage output in the destination filesystem and atomically replace
the EPUB only after a successful build. A failed or interrupted conversion
leaves the existing destination intact. Existing file mode bits are preserved;
explicit destination symlinks resolve to their target. Pandoc may download on
first EPUB2 use, as documented in the README. The checksum-verified native
binary uses the OS user cache or `DOCS2EPUB_CACHE_DIR`; EPUB3 avoids Pandoc.

## Compatibility and distribution

The human completion summary remains available. Progress and Pandoc warnings
now go to stderr; scripts needing metadata should use the documented JSON
summary. The package remains installable with `uvx docs2epub`; this change does
not publish a package or tag a release. A single-action URL-to-file converter
does not need subcommands or a pager. Full terminal help and web documentation
serve the documentation needs without a separate man page.

## Verification

`uv run --extra dev pytest -q` runs offline fixture tests, including CLI help,
validation, stdout/stderr, JSON, binary output, dry runs, request timeouts,
interruption, and failed-write preservation. `uv build` checks packaging.
Live documentation-site behavior is separate from these deterministic CLI
contracts and can be checked manually with a disposable destination.
