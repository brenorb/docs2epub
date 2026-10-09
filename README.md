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
