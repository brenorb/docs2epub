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

  p.add_argument(
    "--start-url",
    required=True,
    help="Starting URL for scraping (initially: Docusaurus docs page).",
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

  p.add_argument(
    "--out",
    required=True,
    help="Output EPUB file path.",
  )

  return p


def main(argv: list[str] | None = None) -> int:
  args = _build_parser().parse_args(argv)

  options = DocusaurusNextOptions(
    start_url=args.start_url,
    base_url=args.base_url,
    max_pages=args.max_pages,
    sleep_s=args.sleep_s,
  )

  chapters = iter_docusaurus_next(options)
  if not chapters:
    raise SystemExit("No chapters scraped (did not find article content).")

  out_path: Path

  if args.format == "epub2":
    out_path = build_epub2_with_pandoc(
      chapters=chapters,
      out_file=Path(args.out),
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
      out_file=Path(args.out),
      meta=meta,
    )

  print(f"Scraped {len(chapters)} pages")
  print(f"EPUB written to: {out_path.resolve()}")
  return 0
