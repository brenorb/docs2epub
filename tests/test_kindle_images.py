import base64

from docs2epub.kindle_images import KindleImageProcessor


PNG_1X1 = base64.b64decode(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+X8sAAAAASUVORK5CYII="
)


class DummyResponse:
  def __init__(self, *, content: bytes, content_type: str) -> None:
    self.content = content
    self.headers = {"content-type": content_type}

  def raise_for_status(self) -> None:
    return None


class DummySession:
  def __init__(self, responses: dict[str, DummyResponse]) -> None:
    self.headers = {}
    self._responses = responses
    self.calls: list[str] = []

  def get(self, url: str, timeout: int = 30) -> DummyResponse:
    self.calls.append(url)
    response = self._responses.get(url)
    if response is None:
      raise AssertionError(f"unexpected url fetch: {url}")
    return response


def test_kindle_image_processor_downloads_and_rewrites_relative_png(tmp_path):
  session = DummySession(
    responses={
      "https://example.com/docs/images/cover.png": DummyResponse(
        content=PNG_1X1,
        content_type="image/png",
      ),
    }
  )
  processor = KindleImageProcessor(assets_dir=tmp_path / "assets", session=session)

  src = processor.rewrite("images/cover.png", base_url="https://example.com/docs/intro")

  assert src is not None
  assert src.startswith("assets/")
  assert (tmp_path / src).exists()


def test_kindle_image_processor_converts_svg_to_png(monkeypatch, tmp_path):
  session = DummySession(
    responses={
      "https://example.com/images/diagram.svg": DummyResponse(
        content=b"<svg></svg>",
        content_type="image/svg+xml",
      ),
    }
  )
  processor = KindleImageProcessor(assets_dir=tmp_path / "assets", session=session)

  monkeypatch.setattr(
    "docs2epub.kindle_images._svg_to_png_bytes",
    lambda raw: PNG_1X1,
  )

  src = processor.rewrite("/images/diagram.svg", base_url="https://example.com/docs/intro")

  assert src is not None
  assert src.endswith(".png")
  assert (tmp_path / src).exists()


def test_kindle_image_processor_caches_downloaded_assets(tmp_path):
  session = DummySession(
    responses={
      "https://example.com/docs/images/cover.png": DummyResponse(
        content=PNG_1X1,
        content_type="image/png",
      ),
    }
  )
  processor = KindleImageProcessor(assets_dir=tmp_path / "assets", session=session)

  a = processor.rewrite("images/cover.png", base_url="https://example.com/docs/intro")
  b = processor.rewrite("images/cover.png", base_url="https://example.com/docs/intro")

  assert a == b
  assert session.calls == ["https://example.com/docs/images/cover.png"]
