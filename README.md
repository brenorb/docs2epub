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

## Optional Kindle email delivery

Add `-k reader@kindle.com` (aliases `--kindle` and `--kindle-email`) to
send the generated EPUB as an attachment. The default remains the existing
Kindle-friendly EPUB2 conversion and metadata. No SMTP configuration is read
unless email delivery is requested.

Configure your SMTP provider through environment variables:

```bash
export DOCS2EPUB_SMTP_HOST=smtp.example.com
export DOCS2EPUB_SMTP_FROM=sender@example.com
export DOCS2EPUB_SMTP_USER=your-smtp-user
# Set DOCS2EPUB_SMTP_PASSWORD through your shell or secret manager.
uvx docs2epub https://example.com/docs book.epub -k reader@kindle.com
```

`DOCS2EPUB_SMTP_SECURITY` defaults to `starttls` with port 587. Set it to
`ssl` for implicit TLS with default port 465. Override either port using
`DOCS2EPUB_SMTP_PORT`. Certificate verification is enabled in both modes.
The user and password must be supplied together; leave both unset for a
provider that accepts authenticated-network relaying over TLS.

Use your own Kindle address and add the `DOCS2EPUB_SMTP_FROM` address to
Amazon's approved personal-document email list. Successful output means the
SMTP server accepted the message; it does not confirm Amazon conversion or
device delivery. If sending fails, the EPUB remains at the printed local path
and the command exits with an error. A Gmail API transport is future work.

## Roadmap

- Add additional discovery strategies: `sitemap.xml`, sidebar parsing, and explicit link lists.
- Optional Gmail API transport for Kindle email delivery.
