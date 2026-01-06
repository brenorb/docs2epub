from docs2epub.epub import EpubMetadata, build_epub
from docs2epub.model import Chapter


def test_build_epub(tmp_path):
  out = tmp_path / "book.epub"
  chapters = [
    Chapter(index=1, title="Hello", url="https://example.com", html="<h1>Hello</h1><p>World</p>"),
  ]
  meta = EpubMetadata(title="T", author="A", language="en")
  path = build_epub(chapters=chapters, out_file=out, meta=meta)
  assert path.exists()
  assert path.stat().st_size > 0
