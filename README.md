# docs2epub

Turn documentation sites into an EPUB (Kindle-friendly).

Initial focus: Docusaurus sites that expose a **Next** button (docs navigation).

When multiple scraped pages link to each other, docs2epub rewrites those links to stay inside the generated EPUB.

## Install (dev)

This project uses Python 3.12+.

```bash
uv sync
uv run docs2epub --help
```

## Usage

Run `docs2epub` for a short introduction, `docs2epub --help` for examples and
all options, or `docs2epub --version` to identify the installed distribution.
Help remains available even when other options are invalid. Long option names
must be written in full, so scripts do not depend on ambiguous abbreviations.

Use `-o` or `--output` as the standard spelling for the output path; `--out`
and the positional output path remain supported. Page requests time out after
30 seconds by default; set `--timeout SECONDS` to change that limit. Invalid
URLs, page limits, delays, and timeouts fail before any network work starts.
Timeouts and inter-page delays are capped at 86400 seconds (one day) to reject
values that cannot be represented safely by networking and sleep APIs.
By default, there is no page limit; use `--max-pages N` with a positive integer
to cap the crawl. `--sleep-s SECONDS` sets the delay between page requests
(default: `0.5`, range: `0` through `86400`; `0` disables the delay).

Progress and Pandoc warnings go to stderr; stdout contains the result. For
scripts, `--json` prints a JSON summary with `ok`, `output`, `pages`,
`size_bytes`, and `format`. Use `-q` / `--quiet` to hide progress while keeping
the result and errors. `Ctrl-C` exits with status 130 and no traceback.
Conversion failures leave an existing destination EPUB intact: completed
output replaces the destination atomically.

Use `-` as the destination to stream binary EPUB bytes to stdout. Redirect or
pipe this stream; writing binary data directly to a terminal is rejected.
Binary stdout and the `--json` summary cannot be combined. A dry run (`-n` /
`--dry-run`) describes the conversion without scraping, downloading Pandoc,
or creating output files. Existing files are atomically replaced on success.

```bash
docs2epub https://example.com/docs book.epub --json > result.json
docs2epub https://example.com/docs book.epub --quiet
docs2epub https://example.com/docs - > book.epub
docs2epub https://example.com/docs book.epub --dry-run
```

See [CLI behavior and design decisions](docs/cli-design.md) for stream,
exit-code, compatibility, and configuration contracts.

### uvx (no install)

EPUB2 uses an existing `pandoc` on your PATH when available. Otherwise,
docs2epub automatically downloads Pandoc 3.12.1 from its official GitHub release,
verifies the archive's SHA-256 checksum, and caches the native executable for
future runs. No separate Homebrew or system installation is required.
The first EPUB2 run needs internet access; subsequent runs reuse the cache.
Automatic installation supports macOS and Linux on Intel/AMD 64-bit and ARM64,
and Windows on Intel/AMD 64-bit. Other platforms can install Pandoc manually
or use `--format epub3`, which uses ebooklib without downloading Pandoc.
Set `DOCS2EPUB_CACHE_DIR` to override the default OS user cache directory.

```bash
uvx docs2epub \
  https://www.techinterviewhandbook.org/software-engineering-interview-guide/ \
  tech-interview-handbook.epub

# Optional (override inferred metadata)
uvx docs2epub \
  https://www.techinterviewhandbook.org/software-engineering-interview-guide/ \
  tech-interview-handbook.epub \
  --title "Tech Interview Handbook" \
  --author "Yangshun Tay"

# Optional: skip images
uvx docs2epub \
  https://www.techinterviewhandbook.org/software-engineering-interview-guide/ \
  tech-interview-handbook.epub \
  --no-images
```

### Docusaurus “Next” crawl

```bash
# Default output is EPUB2 (Kindle-friendly) via pandoc
uv run docs2epub \
  --start-url "https://www.techinterviewhandbook.org/software-engineering-interview-guide/" \
  --out "dist/tech-interview-handbook.epub" \
  --title "Tech Interview Handbook" \
  --author "Yangshun Tay"

# Optional: build EPUB3 (ebooklib)
uv run docs2epub \
  --format epub3 \
  --start-url "https://www.techinterviewhandbook.org/software-engineering-interview-guide/" \
  --out "dist/tech-interview-handbook.epub" \
  --title "Tech Interview Handbook" \
  --author "Yangshun Tay"
```

## Roadmap

- Add additional discovery strategies: `sitemap.xml`, sidebar parsing, and explicit link lists.
- Optional: send-to-kindle (email), once Gmail auth is set up.
