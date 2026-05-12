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


def test_iter_preserves_original_scope_after_canonical_refetch(monkeypatch):
  start_url = "https://example.com/"
  canonical = "https://example.com/home"
  sidebar = """
  <nav class="menu">
    <a href="/home">Home</a>
    <a href="/specification">Specification</a>
  </nav>
  """
  pages = {
    start_url: (
      200,
      (
        "<html><head>"
        f'<link rel="canonical" href="{canonical}" />'
        "</head><body><article><h1>Landing</h1></article></body></html>"
      ),
    ),
    canonical: (
      200,
      f"<html><body>{sidebar}<article><h1>Home</h1><p>Welcome</p></article></body></html>",
    ),
    "https://example.com/specification": (
      200,
      (
        f"<html><body>{sidebar}<article><h1>Specification</h1>"
        "<p>Details</p></article></body></html>"
      ),
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Home", "Specification"]


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


def test_iter_falls_back_to_body_when_no_article(monkeypatch):
  start_url = "https://example.com/book"
  pages = {
    start_url: (
      200,
      "<html><body><h1>Book</h1><p>All content here</p></body></html>",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Book"]


def test_iter_resolves_relative_image_sources_against_page_url(monkeypatch):
  start_url = "https://example.com/docs/intro"
  pages = {
    start_url: (
      200,
      (
        "<html><body>"
        "<article><h1>Intro</h1><img src=\"images/diagram.png\" /></article>"
        "</body></html>"
      ),
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert len(chapters) == 1
  assert 'src="https://example.com/docs/images/diagram.png"' in chapters[0].html


def test_iter_uses_llms_index_when_no_sidebar(monkeypatch):
  start_url = "https://example.com/"
  pages = {
    start_url: (
      200,
      (
        "<html><body><main><h1>Agent Skills</h1>"
        '<p><a href="/llms.txt">Documentation Index</a></p>'
        "</main></body></html>"
      ),
    ),
    "https://example.com/llms.txt": (
      200,
      (
        "# Docs\n\n"
        "- [Overview](https://example.com/home.md)\n"
        "- [Quickstart](https://example.com/quickstart.md)\n"
      ),
    ),
    "https://example.com/home.md": (
      200,
      (
        "> ## Documentation Index\n"
        "> Fetch the complete documentation index at: https://example.com/llms.txt\n"
        "> Use this file to discover all available pages before exploring further.\n\n"
        "# Overview\n\nWelcome to the docs.\n"
      ),
    ),
    "https://example.com/quickstart.md": (
      200,
      (
        "> ## Documentation Index\n"
        "> Fetch the complete documentation index at: https://example.com/llms.txt\n"
        "> Use this file to discover all available pages before exploring further.\n\n"
        "# Quickstart\n\nRun the setup.\n"
      ),
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == ["Overview", "Quickstart"]
  assert "Welcome to the docs." in chapters[0].html
  assert "Run the setup." in chapters[1].html


def test_iter_scrapes_markdown_files_from_github_tree(monkeypatch):
  start_url = "https://github.com/acme/book/tree/main/content"
  first_raw = "https://github.com/acme/book/raw/refs/heads/main/content/01-intro.md"
  alias_raw = "https://github.com/acme/book/raw/refs/heads/main/content/1-intro.md"
  second_raw = "https://github.com/acme/book/raw/refs/heads/main/content/02-prompts.md"
  pages = {
    start_url: (
      200,
      (
        "<html><body><main><h1>content</h1></main>"
        '<script type="application/json" data-target="react-app.embeddedData">'
        '{"payload":{"codeViewTreeRoute":{"path":"content","refInfo":{"name":"main","refType":"branch"},"tree":{"items":['
        '{"name":"01-intro.md","path":"content/01-intro.md","contentType":"file"},'
        '{"name":"1-intro.md","path":"content/1-intro.md","contentType":"file"},'
        '{"name":"images","path":"content/images","contentType":"directory"},'
        '{"name":"02-prompts.md","path":"content/02-prompts.md","contentType":"file"}'
        "]}}}}"
        "</script></body></html>"
      ),
    ),
    first_raw: (
      200,
      "# 1. Natural Language to Tool Calls\n\nIntro text\n",
    ),
    alias_raw: (
      200,
      "[Moved to 01-intro.md](./01-intro.md)\n",
    ),
    second_raw: (
      200,
      "## 2. Own Your Prompts\n\nPrompt text\n",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == [
    "1. Natural Language to Tool Calls",
    "2. Own Your Prompts",
  ]
  assert [c.url for c in chapters] == [first_raw, second_raw]
  assert "Intro text" in chapters[0].html
  assert "Prompt text" in chapters[1].html
  assert len(chapters) == 2


def test_iter_fetches_github_blob_markdown_from_raw_url(monkeypatch):
  start_url = "https://github.com/acme/book/blob/main/content/01-intro.md"
  raw_url = "https://github.com/acme/book/raw/refs/heads/main/content/01-intro.md"
  pages = {
    start_url: (
      200,
      (
        "<html><body><main>"
        '<a data-testid="raw-button" href="https://github.com/acme/book/raw/refs/heads/main/content/01-intro.md">'
        "Raw</a>"
        "</main></body></html>"
      ),
    ),
    raw_url: (
      200,
      "# 1. Natural Language to Tool Calls\n\nRendered markdown body\n",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert len(chapters) == 1
  assert chapters[0].title == "1. Natural Language to Tool Calls"
  assert "Rendered markdown body" in chapters[0].html
  assert chapters[0].url == raw_url
  assert "<h1>1. Natural Language to Tool Calls</h1>" not in chapters[0].html


def test_iter_orders_github_tree_markdown_like_a_book(monkeypatch):
  start_url = "https://github.com/acme/book/tree/main/content"
  pages = {
    start_url: (
      200,
      (
        "<html><body>"
        '<script type="application/json" data-target="react-app.embeddedData">'
        '{"payload":{"codeViewTreeRoute":{"path":"content","refInfo":{"name":"main","refType":"branch"},"tree":{"items":['
        '{"name":"appendix-13-pre-fetch.md","path":"content/appendix-13-pre-fetch.md","contentType":"file"},'
        '{"name":"brief-history-of-software.md","path":"content/brief-history-of-software.md","contentType":"file"},'
        '{"name":"factor-02-own-your-prompts.md","path":"content/factor-02-own-your-prompts.md","contentType":"file"},'
        '{"name":"factor-01-natural-language-to-tool-calls.md","path":"content/factor-01-natural-language-to-tool-calls.md","contentType":"file"}'
        "]}}}}"
        "</script></body></html>"
      ),
    ),
    "https://github.com/acme/book/raw/refs/heads/main/content/appendix-13-pre-fetch.md": (
      200,
      "# Appendix\n\nAppendix text\n",
    ),
    "https://github.com/acme/book/raw/refs/heads/main/content/brief-history-of-software.md": (
      200,
      "# Brief history\n\nHistory text\n",
    ),
    "https://github.com/acme/book/raw/refs/heads/main/content/factor-02-own-your-prompts.md": (
      200,
      "# Factor 2\n\nPrompts text\n",
    ),
    "https://github.com/acme/book/raw/refs/heads/main/content/factor-01-natural-language-to-tool-calls.md": (
      200,
      "# Factor 1\n\nIntro text\n",
    ),
  }

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: _make_session_with_status(pages)(),
  )

  options = DocusaurusNextOptions(start_url=start_url, sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert [c.title for c in chapters] == [
    "Brief history",
    "Factor 1",
    "Factor 2",
    "Appendix",
  ]
