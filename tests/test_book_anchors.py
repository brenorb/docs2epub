from zipfile import ZipFile

from bs4 import BeautifulSoup

from docs2epub.docusaurus_next import _remove_title_heading
from docs2epub.epub import EpubMetadata, build_epub
from docs2epub.model import Chapter


def test_crawler_keeps_title_anchor_after_removing_duplicate_heading():
  soup = BeautifulSoup('<article><h1 id="overview">Overview</h1><p>Body</p></article>', "lxml")
  _remove_title_heading(soup.article, "Overview")
  assert soup.find("h1") is None
  assert soup.find(id="overview") is not None
  assert soup.article.get_text(strip=True) == "Body"


def test_epub3_rewritten_title_link_has_a_live_target(tmp_path):
  out = tmp_path / "book.epub"
  chapters = [
    Chapter(index=1, title="Intro", url="https://example.com/docs/intro",
      html='<p><a href="../next/?tracking=1#overview">Next overview</a></p>'),
    Chapter(index=2, title="Overview", url="https://example.com/next",
      html='<h1 id="overview">Overview</h1><p>Body</p>'),
  ]
  build_epub(chapters=chapters, out_file=out, meta=EpubMetadata(title="Guide", author="Author"))
  with ZipFile(out) as archive:
    first = BeautifulSoup(archive.read("EPUB/chap_001.xhtml"), "xml")
    second = BeautifulSoup(archive.read("EPUB/chap_002.xhtml"), "xml")
  assert first.find("a")["href"] == "chap_002.xhtml#overview"
  assert second.find(id="overview") is not None
  assert len(second.find_all("h1")) == 1


def test_global_links_and_duplicate_ids_are_scoped_per_chapter():
  from docs2epub.book_links import namespace_html_ids, rewrite_internal_book_links
  targets = {"https://example.com/one": "#chapter-one", "https://example.com/two": "#chapter-two"}
  source = '<h2 id="details">Details</h2><a href="#details">Local</a><a href="/two#details">Other</a><a href="/two">Chapter</a><a href="https://elsewhere.test/page#details">External</a>'
  first = BeautifulSoup(rewrite_internal_book_links(namespace_html_ids(source, "chapter-one"),
    current_url="https://example.com/one", chapter_file_by_url=targets), "lxml")
  second = BeautifulSoup(namespace_html_ids('<h2 id="details">Details</h2>', "chapter-two"), "lxml")
  links = {a.get_text(): a["href"] for a in first.find_all("a")}
  assert first.find(id=links["Local"][1:]) is not None
  assert second.find(id=links["Other"][1:]) is not None
  assert links["Chapter"] == "#chapter-two"
  assert links["External"] == "https://elsewhere.test/page#details"
  assert {el["id"] for el in first.find_all(id=True)}.isdisjoint({el["id"] for el in second.find_all(id=True)})
