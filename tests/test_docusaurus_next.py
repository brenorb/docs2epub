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
