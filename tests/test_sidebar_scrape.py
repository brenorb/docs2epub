import requests

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


def _make_session_with_status(pages: dict[str, tuple[int, str]]):
  class DummyResponse:
    def __init__(self, url: str, status_code: int, text: str) -> None:
      self.url = url
      self.status_code = status_code
      self.text = text

    def raise_for_status(self) -> None:
      if self.status_code >= 400:
        raise requests.HTTPError(
          f"{self.status_code} Client Error",
          response=self,
        )

  class DummySession:
    def __init__(self) -> None:
      self.headers = {}

    def get(self, url: str, timeout: int = 30) -> DummyResponse:
      if url not in pages:
        raise AssertionError(f"unexpected url fetch: {url}")
      status_code, text = pages[url]
      return DummyResponse(url, status_code, text)

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


def test_iter_skips_sidebar_links_that_404(monkeypatch):
  start_url = "https://example.com/docs/intro"
  sidebar = """
  <nav class="menu">
    <a class="menu__link" href="/docs/intro">Intro</a>
    <a class="menu__link" href="/docs/missing">Missing</a>
    <a class="menu__link" href="/docs/other">Other</a>
  </nav>
  """
  pages = {
    start_url: (
      200,
      f"<html><body>{sidebar}<article><h1>Intro</h1><p>Intro text</p></article></body></html>",
    ),
    "https://example.com/docs/missing": (404, "Not found"),
    "https://example.com/docs/other": (
      200,
      f"<html><body>{sidebar}<article><h1>Other</h1><p>Other text</p></article></body></html>",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Intro", "Other"]


def test_iter_resolves_links_against_canonical(monkeypatch):
  start_url = "https://example.com/"
  canonical = "https://example.com/en/stable/index.html"
  sidebar = """
  <nav class="bd-links bd-docs-nav">
    <a class="reference internal" href="usage/quickstart.html">Quickstart</a>
    <a class="reference internal" href="usage/install.html">Install</a>
  </nav>
  """
  pages = {
    start_url: (
      200,
      (
        "<html><head>"
        f'<link rel="canonical" href="{canonical}" />'
        "</head><body>"
        f"{sidebar}<main><h1>Home</h1><p>Welcome</p></main>"
        "</body></html>"
      ),
    ),
    canonical: (
      200,
      (
        "<html><body>"
        f"{sidebar}<main><h1>Home</h1><p>Welcome</p></main>"
        "</body></html>"
      ),
    ),
    "https://example.com/en/stable/usage/quickstart.html": (
      200,
      f"<html><body>{sidebar}<article><h1>Quickstart</h1></article></body></html>",
    ),
    "https://example.com/en/stable/usage/install.html": (
      200,
      f"<html><body>{sidebar}<article><h1>Install</h1></article></body></html>",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Home", "Quickstart", "Install"]


def test_iter_refetches_canonical_for_sidebar(monkeypatch):
  start_url = "https://example.com/"
  canonical = "https://example.com/en/stable/index.html"
  pages = {
    start_url: (
      200,
      (
        "<html><head>"
        f'<link rel="canonical" href="{canonical}" />'
        "</head><body><article><h1>Home</h1></article></body></html>"
      ),
    ),
    canonical: (
      200,
      (
        '<html><body><nav class="menu">'
        '<a href="/en/stable/one.html">One</a>'
        "</nav><article><h1>Home</h1></article></body></html>"
      ),
    ),
    "https://example.com/en/stable/one.html": (
      200,
      "<html><body><article><h1>One</h1></article></body></html>",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Home", "One"]


def test_iter_skips_pages_without_article(monkeypatch):
  start_url = "https://example.com/docs/intro"
  sidebar = """
  <nav class="menu">
    <a class="menu__link" href="/docs/intro">Intro</a>
    <a class="menu__link" href="/docs/console">Console</a>
    <a class="menu__link" href="/docs/other">Other</a>
  </nav>
  """
  pages = {
    start_url: (
      200,
      f"<html><body>{sidebar}<article><h1>Intro</h1><p>Intro text</p></article></body></html>",
    ),
    "https://example.com/docs/console": (200, "<html><body><div>App shell</div></body></html>"),
    "https://example.com/docs/other": (
      200,
      f"<html><body>{sidebar}<article><h1>Other</h1><p>Other text</p></article></body></html>",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Intro", "Other"]
