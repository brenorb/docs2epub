from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from .docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next
from .epub import EpubMetadata, build_epub
from .pandoc_epub2 import PandocEpub2Options, build_epub2_with_pandoc


def _infer_defaults(start_url: str) -> tuple[str, str, str]:
  parsed = urlparse(start_url)
  host = parsed.netloc or "docs"
  title = host
  author = host
  language = "en"
  return title, author, language


def _build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="docs2epub",
    description="Turn documentation sites into an EPUB (Kindle-friendly).",
  )

  # Short positional form (for uvx):
  #   docs2epub <START_URL> <OUT.epub>
  p.add_argument(
    "start_url_pos",
    nargs="?",
    help="Starting URL for scraping (initially: Docusaurus docs page).",
  )
  p.add_argument(
    "out_pos",
    nargs="?",
    help="Output EPUB file path.",
  )

  # Flag form (more explicit):
  p.add_argument(
    "--start-url",
    dest="start_url",
    default=None,
    help="Starting URL for scraping (overrides positional start_url).",
  )
  p.add_argument(
    "--out",
    dest="out",
    default=None,
    help="Output EPUB file path (overrides positional out).",
  )

  p.add_argument(
    "--base-url",
    default=None,
    help="Base URL used to resolve relative links (defaults to start-url).",
  )
  p.add_argument("--max-pages", type=int, default=None)
  p.add_argument("--sleep-s", type=float, default=0.5)

  p.add_argument("--title", default=None)
  p.add_argument("--author", default=None)
  p.add_argument("--language", default=None)
  p.add_argument("--identifier", default=None)
  p.add_argument("--publisher", default=None)

  p.add_argument(
    "--format",
    default="epub2",
    choices=["epub2", "epub3"],
    help="Output format. Default: epub2 (Kindle-friendly).",
  )

  p.add_argument(
    "--keep-images",
    action="store_true",
    help="Keep and embed remote images (may be slower and can trigger fetch warnings).",
  )

  p.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Verbose output (shows full pandoc warnings).",
  )

  return p


def main(argv: list[str] | None = None) -> int:
  args = _build_parser().parse_args(argv)

  start_url = args.start_url or args.start_url_pos
  out_value = args.out or args.out_pos

  if not start_url or not out_value:
    raise SystemExit("Usage: docs2epub <START_URL> <OUT.epub> [options]")

  inferred_title, inferred_author, inferred_language = _infer_defaults(start_url)

  title = args.title or inferred_title
  author = args.author or inferred_author
  language = args.language or inferred_language

  options = DocusaurusNextOptions(
    start_url=start_url,
    base_url=args.base_url,
    max_pages=args.max_pages,
    sleep_s=args.sleep_s,
  )

  chapters = iter_docusaurus_next(options)
  if not chapters:
    raise SystemExit("No pages scraped (did not find article content).")

  out_path_value = Path(out_value)

  if args.format == "epub2":
    out_path = build_epub2_with_pandoc(
      chapters=chapters,
      out_file=out_path_value,
      title=title,
      author=author,
      language=language,
      publisher=args.publisher,
      identifier=args.identifier,
      verbose=args.verbose,
      options=PandocEpub2Options(keep_images=args.keep_images),
    )
  else:
    meta = EpubMetadata(
      title=title,
      author=author,
      language=language,
      identifier=args.identifier,
      publisher=args.publisher,
    )

    out_path = build_epub(
      chapters=chapters,
      out_file=out_path_value,
      meta=meta,
    )

  size_mb = out_path.stat().st_size / (1024 * 1024)
  print(f"Scraped {len(chapters)} pages")
  print(f"EPUB written to: {out_path.resolve()} ({size_mb:.2f} MB)")
  return 0
