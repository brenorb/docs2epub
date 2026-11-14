import requests

from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next


def test_iter_docusaurus_next_falls_back_to_main_when_no_article(monkeypatch):
  html = """
  <!doctype html>
  <html>
    <body>
      <main>
        <div>
          <h1>Overview</h1>
          <p>Hello world</p>
        </div>
      </main>
    </body>
  </html>
  """

  class DummyResponse:
    text = html

    def raise_for_status(self) -> None:
      return None

  class DummySession:
    def __init__(self) -> None:
      self.headers = {}

    def get(self, url: str, timeout: int = 30) -> DummyResponse:
      return DummyResponse()

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: DummySession(),
  )

  options = DocusaurusNextOptions(start_url="https://example.com/docs", sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert len(chapters) == 1
  assert chapters[0].title == "Overview"
  assert "Hello world" in chapters[0].html


def test_iter_docusaurus_next_uses_content_area_container(monkeypatch):
  html = """
  <!doctype html>
  <html>
    <body>
      <div id="content-area">
        <header><h1>Specification</h1></header>
        <p>Rendered docs content.</p>
      </div>
    </body>
  </html>
  """

  class DummyResponse:
    text = html

    def raise_for_status(self) -> None:
      return None

  class DummySession:
    def __init__(self) -> None:
      self.headers = {}

    def get(self, url: str, timeout: int = 30) -> DummyResponse:
      return DummyResponse()

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: DummySession(),
  )

  options = DocusaurusNextOptions(start_url="https://example.com/specification", sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert len(chapters) == 1
  assert chapters[0].title == "Specification"
  assert "Rendered docs content." in chapters[0].html


def test_iter_docusaurus_next_strips_documentation_index_from_rendered_container(monkeypatch):
  html = """
  <!doctype html>
  <html>
    <body>
      <div id="content-area">
        <header><h1>Specification</h1></header>
        <blockquote>
          <p>Documentation Index</p>
          <p>Fetch the complete documentation index at: https://example.com/llms.txt</p>
        </blockquote>
        <p>Rendered docs content.</p>
      </div>
    </body>
  </html>
  """

  class DummyResponse:
    text = html

    def raise_for_status(self) -> None:
      return None

  class DummySession:
    def __init__(self) -> None:
      self.headers = {}

    def get(self, url: str, timeout: int = 30) -> DummyResponse:
      return DummyResponse()

  monkeypatch.setattr(
    "docs2epub.docusaurus_next.requests.Session",
    lambda: DummySession(),
  )

  options = DocusaurusNextOptions(start_url="https://example.com/specification", sleep_s=0)
  chapters = iter_docusaurus_next(options)

  assert len(chapters) == 1
  assert chapters[0].title == "Specification"
  assert "Documentation Index" not in chapters[0].html
  assert "Rendered docs content." in chapters[0].html


def test_next_crawl_stops_fetching_at_chapter_limit(monkeypatch):
  start_url = "https://example.com/docs/intro"
  next_url = "https://example.com/docs/second"
  fetched = []

  def get(_session, url, *, timeout):
    fetched.append(url)
    response = requests.Response()
    response.url = url
    if url == start_url:
      response.status_code = 200
      response._content = (
        b'<article><h1>Intro</h1><p>First chapter</p></article>'
        b'<nav aria-label="Docs pages"><a href="/docs/second">Next</a></nav>'
      )
    else:
      assert url == next_url
      response.status_code = 503
    return response

  monkeypatch.setattr(requests.Session, "get", get)
  options = DocusaurusNextOptions(start_url=start_url, max_pages=1, sleep_s=0)

  chapters = iter_docusaurus_next(options)

  assert [chapter.title for chapter in chapters] == ["Intro"]
  assert fetched == [start_url]
