from docs2epub.epub import EpubMetadata, build_epub
from docs2epub.kindle_html import clean_html_for_kindle_epub2
from docs2epub.model import Chapter


def test_build_epub3_smoke(tmp_path):
  out = tmp_path / "book.epub"
  chapters = [
    Chapter(index=1, title="Hello", url="https://example.com", html="<h1>Hello</h1><p>World</p>"),
  ]
  meta = EpubMetadata(title="T", author="A", language="en")
  path = build_epub(chapters=chapters, out_file=out, meta=meta)
  assert path.exists()
  assert path.stat().st_size > 0


def test_kindle_cleaner_strips_tabindex_and_ol_start():
  cleaned = clean_html_for_kindle_epub2(
    '<div tabindex="0"><ol start="2"><li><u>Hi</u></li></ol></div>',
    keep_images=False,
  )
  assert "tabindex" not in cleaned
  assert "start=" not in cleaned
  assert "underline" in cleaned


def test_kindle_cleaner_drops_remote_images_by_default():
  cleaned = clean_html_for_kindle_epub2(
    '<p>x</p><img src="https://example.com/a.png" /><p>y</p>',
    keep_images=False,
  )
  assert "img" not in cleaned
