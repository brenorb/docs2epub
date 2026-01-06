from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .kindle_html import clean_html_for_kindle_epub2
from .model import Chapter


@dataclass(frozen=True)
class PandocEpub2Options:
  toc: bool = True
  toc_depth: int = 2
  split_level: int = 1
  keep_images: bool = False


def _wrap_html(title: str, body_html: str) -> str:
  return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{title}</title>
  </head>
  <body>
    <h1>{title}</h1>
    {body_html}
  </body>
</html>
"""


def _summarize_pandoc_warnings(stderr: str) -> str:
  warnings = [line for line in stderr.splitlines() if line.startswith("[WARNING]")]
  if not warnings:
    return ""

  resource = [w for w in warnings if "Could not fetch resource" in w]
  duplicate = [w for w in warnings if "Duplicate identifier" in w]

  parts: list[str] = []
  parts.append(f"pandoc warnings: {len(warnings)} (use -v to see full output)")
  if duplicate:
    parts.append(f"- Duplicate identifier: {len(duplicate)} (usually safe; affects internal anchors)")
  if resource:
    parts.append(
      f"- Missing resources: {len(resource)} (some images may be dropped; use --keep-images/-v to inspect)"
    )

  return "\n".join(parts)


def build_epub2_with_pandoc(
  *,
  chapters: Iterable[Chapter],
  out_file: str | Path,
  title: str,
  author: str,
  language: str,
  publisher: str | None,
  identifier: str | None,
  verbose: bool,
  options: PandocEpub2Options | None = None,
) -> Path:
  pandoc = shutil.which("pandoc")
  if not pandoc:
    raise RuntimeError(
      "pandoc not found. Install pandoc (https://pandoc.org/installing.html) or use --format epub3."
    )

  opts = options or PandocEpub2Options()

  out_path = Path(out_file)
  out_path.parent.mkdir(parents=True, exist_ok=True)

  with tempfile.TemporaryDirectory(prefix="docs2epub-pandoc-") as tmp:
    tmp_path = Path(tmp)

    html_files: list[Path] = []
    for ch in chapters:
      cleaned = clean_html_for_kindle_epub2(ch.html, keep_images=opts.keep_images)
      html_doc = _wrap_html(ch.title, cleaned)
      fp = tmp_path / f"chapter_{ch.index:04d}.html"
      fp.write_text(html_doc, encoding="utf-8")
      html_files.append(fp)

    cmd: list[str] = [
      pandoc,
      "--to",
      "epub2",
      "--metadata",
      f"title={title}",
      "--metadata",
      f"author={author}",
      "--metadata",
      f"language={language}",
      "--metadata",
      "encoding=UTF-8",
      "--standalone",
      "--split-level",
      str(opts.split_level),
    ]

    if publisher:
      cmd.extend(["--metadata", f"publisher={publisher}"])

    if identifier:
      # Keep identifier stable for Kindle.
      cmd.extend(["--metadata", f"identifier={identifier}"])

    if opts.toc:
      cmd.extend(["--toc", "--toc-depth", str(opts.toc_depth)])

    cmd.extend(["-o", str(out_path)])
    cmd.extend([str(p) for p in html_files])

    proc = subprocess.run(
      cmd,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
    )

    if proc.returncode != 0:
      # On failure, always show stderr.
      raise RuntimeError(f"pandoc failed (exit {proc.returncode}):\n{proc.stderr.strip()}")

    if verbose and proc.stderr.strip():
      print(proc.stderr.strip())
    elif proc.stderr.strip():
      summary = _summarize_pandoc_warnings(proc.stderr)
      if summary:
        print(summary)

  return out_path
