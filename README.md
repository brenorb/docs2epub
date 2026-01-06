# docs2epub

Turn documentation sites into an EPUB (Kindle-friendly).

Initial focus: Docusaurus sites that expose a **Next** button (docs navigation).

## Install (dev)

This project uses Python 3.12+.

```bash
uv sync
uv run docs2epub --help
```

## Usage

### uvx (no install)

```bash
uvx docs2epub \
  https://www.techinterviewhandbook.org/software-engineering-interview-guide/ \
  tech-interview-handbook.epub \
  --title "Tech Interview Handbook" \
  --author "Yangshun Tay"
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
