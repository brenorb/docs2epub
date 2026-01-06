from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from ebooklib import epub

from .model import Chapter


EPUB_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.55;
}
pre, code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  background: #f7f7f7;
}
.chapter-sep {
  margin-top: 1.75rem;
  border-top: 1px solid #ddd;
}
"""


@dataclass(frozen=True)
class EpubMetadata:
  title: str
  author: str
  language: str = "en"
  identifier: str | None = None
  publisher: str | None = None
  created_at: datetime | None = None


def _extract_body_inner_html(html: str) -> str:
  soup = BeautifulSoup(html, "lxml")
  body = soup.find("body")
  if not body:
    return html
  return body.decode_contents()


def _strip_first_h1(html_fragment: str) -> str:
  soup = BeautifulSoup(html_fragment, "lxml")
  first_h1 = soup.find("h1")
  if first_h1:
    first_h1.decompose()
  body = soup.find("body")
  if body:
    return body.decode_contents()
  return str(soup)


def build_epub(
  *,
  chapters: Iterable[Chapter],
  out_file: str | Path,
  meta: EpubMetadata,
) -> Path:
  out_path = Path(out_file)
  out_path.parent.mkdir(parents=True, exist_ok=True)

  book = epub.EpubBook()

  identifier = meta.identifier or f"urn:uuid:{uuid.uuid4()}"
  book.set_identifier(identifier)
  book.set_title(meta.title)
  book.set_language(meta.language)
  book.add_author(meta.author)

  if meta.publisher:
    book.add_metadata("DC", "publisher", meta.publisher)

  created_at = meta.created_at or datetime.now(timezone.utc)
  book.add_metadata("DC", "date", created_at.isoformat())

  style_item = epub.EpubItem(
    uid="style_nav",
    file_name="style/style.css",
    media_type="text/css",
    content=EPUB_CSS.encode("utf-8"),
  )
  book.add_item(style_item)

  chapter_items: list[epub.EpubHtml] = []
  toc_items: list[epub.Link] = []

  for ch in chapters:
    body_inner = _extract_body_inner_html(ch.html)
    body_inner = _strip_first_h1(body_inner)

    content = f"""<h1>{ch.title}</h1>
<div class=\"chapter-sep\"></div>
{body_inner}
"""

    item = epub.EpubHtml(
      title=ch.title,
      file_name=f"chap_{ch.index:03d}.xhtml",
      lang=meta.language,
    )
    item.content = content
    item.add_item(style_item)

    book.add_item(item)
    chapter_items.append(item)
    toc_items.append(epub.Link(item.file_name, ch.title, f"chap_{ch.index:03d}"))

  book.toc = tuple(toc_items)
  book.spine = ["nav", *chapter_items]

  book.add_item(epub.EpubNcx())
  book.add_item(epub.EpubNav())

  epub.write_epub(str(out_path), book, {})
  return out_path
