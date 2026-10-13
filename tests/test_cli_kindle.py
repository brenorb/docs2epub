from pathlib import Path

import pytest

from docs2epub import cli
from docs2epub.model import Chapter


def fake_book(monkeypatch):
  monkeypatch.setattr(cli, "iter_docusaurus_next", lambda options: [
    Chapter(index=1, title="Intro", url="https://example.com/docs", html="<p>Body</p>")])
  def build(**kwargs):
    path = Path(kwargs["out_file"])
    path.write_bytes(b"epub")
    return path
  monkeypatch.setattr(cli, "build_epub2_with_pandoc", build)


@pytest.mark.parametrize("flag", ["-k", "--kindle", "--kindle-email"])
def test_cli_sends_generated_epub_only_when_requested(monkeypatch, tmp_path, flag, capsys):
  fake_book(monkeypatch)
  monkeypatch.setenv("DOCS2EPUB_SMTP_HOST", "smtp.example.com")
  monkeypatch.setenv("DOCS2EPUB_SMTP_FROM", "sender@example.com")
  sent = []
  monkeypatch.setattr(cli, "send_epub_to_kindle", lambda *args: sent.append(args), raising=False)
  path = tmp_path / "book.epub"
  assert cli.main(["https://example.com/docs", str(path), flag, "reader@kindle.com"]) == 0
  assert len(sent) == 1
  assert sent[0][0] == path
  assert sent[0][1] == "reader@kindle.com"
  assert sent[0][0].read_bytes() == b"epub"
  assert "SMTP server accepted" in capsys.readouterr().out


def test_cli_default_requires_no_smtp_settings(monkeypatch, tmp_path):
  fake_book(monkeypatch)
  monkeypatch.delenv("DOCS2EPUB_SMTP_HOST", raising=False)
  monkeypatch.setattr(cli, "send_epub_to_kindle", lambda *a: pytest.fail("must not send"), raising=False)
  assert cli.main(["https://example.com/docs", str(tmp_path / "book.epub")]) == 0


def test_cli_invalid_email_configuration_fails_before_scraping(monkeypatch, tmp_path):
  monkeypatch.delenv("DOCS2EPUB_SMTP_HOST", raising=False)
  monkeypatch.setattr(cli, "iter_docusaurus_next", lambda *a: pytest.fail("must not scrape"))
  with pytest.raises(SystemExit, match="DOCS2EPUB_SMTP_HOST"):
    cli.main(["https://example.com/docs", str(tmp_path / "book.epub"), "-k", "reader@kindle.com"])


def test_cli_failed_email_preserves_generated_epub(monkeypatch, tmp_path, capsys):
  fake_book(monkeypatch)
  monkeypatch.setenv("DOCS2EPUB_SMTP_HOST", "smtp.example.com")
  monkeypatch.setenv("DOCS2EPUB_SMTP_FROM", "sender@example.com")
  def fail(*args): raise RuntimeError("SMTP delivery failed; EPUB saved locally.")
  monkeypatch.setattr(cli, "send_epub_to_kindle", fail, raising=False)
  path = tmp_path / "book.epub"
  with pytest.raises(SystemExit, match="SMTP delivery failed"):
    cli.main(["https://example.com/docs", str(path), "-k", "reader@kindle.com"])
  assert path.read_bytes() == b"epub"
  assert "EPUB written to" in capsys.readouterr().out
