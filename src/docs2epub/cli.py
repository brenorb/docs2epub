from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlparse

import requests

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
    allow_abbrev=False,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""Examples:
  docs2epub https://example.com/docs book.epub
  docs2epub https://example.com/docs book.epub --format epub3 --no-images

Documentation: https://github.com/brenorb/docs2epub#readme
Issues: https://github.com/brenorb/docs2epub/issues""",
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
    "-o", "--output",
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
  p.add_argument("--timeout", type=float, default=30.0, help="Page request timeout in seconds (default: 30).")
  p.add_argument("--version", action="version", version=f"docs2epub {version('docs2epub')}")
  p.add_argument("--json", action="store_true", help="Print a JSON result summary to stdout.")
  p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages; keep the result and errors.")

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

  p.set_defaults(keep_images=True)
  p.add_argument(
    "--keep-images",
    dest="keep_images",
    action="store_true",
    help="Keep and embed images (default).",
  )
  p.add_argument(
    "--no-images",
    dest="keep_images",
    action="store_false",
    help="Drop images for a smaller/faster output.",
  )

  p.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Verbose output (shows full pandoc warnings).",
  )

  return p


def main(argv: list[str] | None = None) -> int:
  parser = _build_parser()
  argv = list(sys.argv[1:] if argv is None else argv)
  if not argv:
    print("Turn documentation sites into an EPUB (Kindle-friendly).\n\n"
          "Usage: docs2epub <START_URL> <OUT.epub> [options]\n\n"
          "Examples:\n  docs2epub https://example.com/docs book.epub\n"
          "  docs2epub https://example.com/docs book.epub --format epub3\n\n"
          "Run docs2epub --help for all options.")
    return 0
  options = argv[:argv.index("--")] if "--" in argv else argv
  if any(flag in options for flag in ("-h", "--help")):
    parser.print_help()
    return 0
  if "--version" in options:
    print(f"docs2epub {version('docs2epub')}")
    return 0
  args = parser.parse_args(argv)

  start_url = args.start_url or args.start_url_pos
  out_value = args.out or args.out_pos

  if not start_url or not out_value:
    parser.error("provide a starting URL and output EPUB path; run docs2epub --help for examples")

  for label, value in (("start URL", start_url), ("base URL", args.base_url)):
    if value is not None:
      parsed = urlparse(value)
      if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        parser.error(f"{label} must be an absolute HTTP or HTTPS URL")
  if args.max_pages is not None and args.max_pages <= 0:
    parser.error("--max-pages must be a positive integer")
  if not math.isfinite(args.sleep_s) or args.sleep_s < 0:
    parser.error("--sleep-s must be a finite nonnegative number")
  if not math.isfinite(args.timeout) or args.timeout <= 0:
    parser.error("--timeout must be a finite positive number")

  inferred_title, inferred_author, inferred_language = _infer_defaults(start_url)

  title = args.title or inferred_title
  author = args.author or inferred_author
  language = args.language or inferred_language

  options = DocusaurusNextOptions(
    start_url=start_url,
    base_url=args.base_url,
    max_pages=args.max_pages,
    sleep_s=args.sleep_s,
    timeout=args.timeout,
  )

  try:
    return _convert(args, options, title, author, language, out_value)
  except KeyboardInterrupt:
    print("Interrupted. The destination EPUB was not partially replaced.", file=sys.stderr)
    return 130
  except BrokenPipeError:
    # Avoid another broken-pipe error when Python flushes stdout at shutdown.
    try:
      fd = os.open(os.devnull, os.O_WRONLY)
      try:
        os.dup2(fd, sys.stdout.fileno())
      finally:
        os.close(fd)
    except (OSError, ValueError):
      pass
    return 0
  except (requests.RequestException, RuntimeError, OSError) as exc:
    raise SystemExit(f"docs2epub: {exc}") from None


def _convert(args, options, title, author, language, out_value) -> int:
  if not args.quiet:
    print(f"Scraping {options.start_url}...", file=sys.stderr, flush=True)
  chapters = iter_docusaurus_next(options)
  if not chapters:
    raise SystemExit("No pages scraped (did not find article content).")

  out_path_value = Path(out_value).expanduser().resolve()
  out_path_value.parent.mkdir(parents=True, exist_ok=True)
  if not args.quiet:
    print(f"Writing {len(chapters)} pages as {args.format.upper()}...", file=sys.stderr, flush=True)

  # Stage in the destination filesystem so failed conversions and interruptions
  # leave existing EPUBs intact, and the final replacement is atomic.
  with tempfile.TemporaryDirectory(prefix=".docs2epub-", dir=out_path_value.parent) as staging:
    staged_path = Path(staging) / out_path_value.name
    if args.format == "epub2":
      out_path = build_epub2_with_pandoc(
        chapters=chapters,
        out_file=staged_path,
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
        out_file=staged_path,
        meta=meta,
      )
    size_bytes = out_path.stat().st_size
    os.replace(out_path, out_path_value)

  if args.json:
    print(json.dumps({"ok": True, "output": str(out_path_value), "pages": len(chapters),
                      "size_bytes": size_bytes, "format": args.format}, indent=2))
  else:
    print(f"EPUB written to: {out_path_value} ({size_bytes / (1024 * 1024):.2f} MB)")
  sys.stdout.flush()
  return 0
