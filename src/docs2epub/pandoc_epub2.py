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
  chapter_level: int = 1


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


def build_epub2_with_pandoc(
  *,
  chapters: Iterable[Chapter],
  out_file: str | Path,
  title: str,
  author: str,
  language: str,
  publisher: str | None,
  identifier: str | None,
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
      cleaned = clean_html_for_kindle_epub2(ch.html)
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
      str(opts.chapter_level),
    ]

    if publisher:
      cmd.extend(["--metadata", f"publisher={publisher}"])

    if identifier:
      cmd.extend(["--epub-metadata", str(identifier)])

    if opts.toc:
      cmd.extend(["--toc", "--toc-depth", str(opts.toc_depth)])

    cmd.extend(["-o", str(out_path)])
    cmd.extend([str(p) for p in html_files])

    subprocess.run(cmd, check=True)

  return out_path
