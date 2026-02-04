from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next


def _make_session(pages: dict[str, str]):
  class DummyResponse:
    def __init__(self, text: str) -> None:
      self.text = text

    def raise_for_status(self) -> None:
      return None

  class DummySession:
    def __init__(self) -> None:
      self.headers = {}

    def get(self, url: str, timeout: int = 30) -> DummyResponse:
      if url not in pages:
        raise AssertionError(f"unexpected url fetch: {url}")
      return DummyResponse(pages[url])

  return DummySession


def test_iter_uses_gitbook_sidebar_links(monkeypatch):
  start_url = "https://example.com/book/intro"
  sidebar = """
  <aside data-testid="table-of-contents">
    <a href="/book/intro">Intro</a>
    <a href="/book/chapter-1">Chapter 1</a>
  </aside>
  """
  pages = {
    start_url: f"<html><body>{sidebar}<main><h1>Intro</h1><p>Intro text</p></main></body></html>",
    "https://example.com/book/chapter-1": f"<html><body>{sidebar}<main><h1>Chapter 1</h1><p>Ch1</p></main></body></html>",
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Intro", "Chapter 1"]


def test_iter_uses_docusaurus_menu_sidebar(monkeypatch):
  start_url = "https://example.com/docs/intro"
  sidebar = """
  <nav class="menu">
    <a class="menu__link" href="/docs/intro">Intro</a>
    <a class="menu__link" href="/docs/install">Install</a>
  </nav>
  """
  pages = {
    start_url: f"<html><body>{sidebar}<article><h1>Intro</h1><p>Intro text</p></article></body></html>",
    "https://example.com/docs/install": f"<html><body>{sidebar}<article><h1>Install</h1><p>Install text</p></article></body></html>",
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Intro", "Install"]


def test_iter_expands_links_from_index_pages(monkeypatch):
  start_url = "https://example.com/docs/intro"
  sidebar = """
  <nav class="menu">
    <a class="menu__link" href="/docs/intro">Intro</a>
    <a class="menu__link" href="/docs/category/getting-started">Getting Started</a>
  </nav>
  """
  pages = {
    start_url: f"<html><body>{sidebar}<article><h1>Intro</h1><p>Intro text</p></article></body></html>",
    "https://example.com/docs/category/getting-started": (
      "<html><body>"
      f"{sidebar}"
      '<article><h1>Getting Started</h1>'
      '<a href="/docs/one">One</a>'
      '<a href="/docs/two">Two</a>'
      "</article></body></html>"
    ),
    "https://example.com/docs/one": f"<html><body>{sidebar}<article><h1>One</h1><p>One text</p></article></body></html>",
    "https://example.com/docs/two": f"<html><body>{sidebar}<article><h1>Two</h1><p>Two text</p></article></body></html>",
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Intro", "Getting Started", "One", "Two"]
