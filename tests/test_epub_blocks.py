from zipfile import ZipFile

from bs4 import BeautifulSoup

from docs2epub.epub import EpubMetadata, build_epub
from docs2epub.model import Chapter


def test_epub3_preserves_paragraph_block_separation(tmp_path):
  out = tmp_path / "book.epub"
  build_epub(chapters=[Chapter(index=1, title="Best Practices", url="https://example.com/docs",
    html='<h3>Provide defaults, not menus</h3><span data-as="p" id="explanation">When multiple tools <em>could work</em>.</span>')],
    out_file=out, meta=EpubMetadata(title="Guide", author="Author"))
  with ZipFile(out) as archive:
    chapter = archive.read("EPUB/chap_001.xhtml")
  soup = BeautifulSoup(chapter, "xml")
  paragraph = soup.find("p", id="explanation")
  assert paragraph is not None
  assert paragraph.find("em").get_text() == "could work"
  assert soup.find("h3").find_next_sibling().name == "p"
  assert soup.find(attrs={"data-as": "p"}) is None
