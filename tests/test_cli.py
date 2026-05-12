from pathlib import Path

import pytest

from docs2epub.cli import _build_parser, main
from docs2epub.model import Chapter


def test_cli_keeps_images_by_default():
  args = _build_parser().parse_args(["https://example.com/docs", "book.epub"])
  assert args.keep_images is True


def test_cli_allows_disabling_images():
  args = _build_parser().parse_args(["https://example.com/docs", "book.epub", "--no-images"])
  assert args.keep_images is False


def test_cli_main_uses_inferred_metadata_for_epub2(monkeypatch, tmp_path, capsys):
  captured: dict[str, object] = {}

  monkeypatch.setattr(
    "docs2epub.cli.iter_docusaurus_next",
    lambda options: [Chapter(index=1, title="Intro", url="https://example.com/docs", html="<p>x</p>")],
  )

  def fake_build_epub2_with_pandoc(**kwargs):
    captured.update(kwargs)
    out_file = Path(kwargs["out_file"])
    out_file.write_bytes(b"epub")
    return out_file

  monkeypatch.setattr("docs2epub.cli.build_epub2_with_pandoc", fake_build_epub2_with_pandoc)

  out_file = tmp_path / "book.epub"
  rc = main(["https://example.com/docs", str(out_file)])

  assert rc == 0
  assert captured["title"] == "example.com"
  assert captured["author"] == "example.com"
  assert captured["language"] == "en"
  assert captured["chapters"][0].title == "Intro"
  assert out_file.exists()
  assert "Scraped 1 pages" in capsys.readouterr().out


def test_cli_main_routes_epub3_to_build_epub(monkeypatch, tmp_path):
  captured: dict[str, object] = {}

  monkeypatch.setattr(
    "docs2epub.cli.iter_docusaurus_next",
    lambda options: [Chapter(index=1, title="Intro", url="https://example.com/docs", html="<p>x</p>")],
  )

  def fake_build_epub(**kwargs):
    captured.update(kwargs)
    out_file = Path(kwargs["out_file"])
    out_file.write_bytes(b"epub3")
    return out_file

  monkeypatch.setattr("docs2epub.cli.build_epub", fake_build_epub)

  out_file = tmp_path / "book.epub"
  rc = main(["--format", "epub3", "--start-url", "https://example.com/docs", "--out", str(out_file)])

  assert rc == 0
  assert captured["meta"].title == "example.com"
  assert captured["meta"].author == "example.com"
  assert captured["meta"].language == "en"
  assert out_file.exists()


def test_cli_main_fails_when_no_pages_are_scraped(monkeypatch, tmp_path):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda options: [])

  with pytest.raises(SystemExit, match="No pages scraped"):
    main(["https://example.com/docs", str(tmp_path / "book.epub")])
