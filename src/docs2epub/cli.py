from __future__ import annotations

import argparse
from pathlib import Path

from .docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next
from .epub import EpubMetadata, build_epub
from .pandoc_epub2 import build_epub2_with_pandoc


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

  p.add_argument("--title", required=True)
  p.add_argument("--author", required=True)
  p.add_argument("--language", default="en")
  p.add_argument("--identifier", default=None)
  p.add_argument("--publisher", default=None)

  p.add_argument(
    "--format",
    default="epub2",
    choices=["epub2", "epub3"],
    help="Output format. Default: epub2 (Kindle-friendly).",
  )

  return p


def main(argv: list[str] | None = None) -> int:
  args = _build_parser().parse_args(argv)

  start_url = args.start_url or args.start_url_pos
  out_value = args.out or args.out_pos

  if not start_url or not out_value:
    raise SystemExit(
      "Usage: docs2epub <START_URL> <OUT.epub> --title ... --author ...\n"
      "(or use --start-url/--out flags)"
    )

  options = DocusaurusNextOptions(
    start_url=start_url,
    base_url=args.base_url,
    max_pages=args.max_pages,
    sleep_s=args.sleep_s,
  )

  chapters = iter_docusaurus_next(options)
  if not chapters:
    raise SystemExit("No chapters scraped (did not find article content).")

  out_path: Path
  out_path_value = Path(out_value)

  if args.format == "epub2":
    out_path = build_epub2_with_pandoc(
      chapters=chapters,
      out_file=out_path_value,
      title=args.title,
      author=args.author,
      language=args.language,
      publisher=args.publisher,
      identifier=args.identifier,
    )
  else:
    meta = EpubMetadata(
      title=args.title,
      author=args.author,
      language=args.language,
      identifier=args.identifier,
      publisher=args.publisher,
    )

    out_path = build_epub(
      chapters=chapters,
      out_file=out_path_value,
      meta=meta,
    )

  print(f"Scraped {len(chapters)} pages")
  print(f"EPUB written to: {out_path.resolve()}")
  return 0
