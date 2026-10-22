"""Offline user-visible command-line contracts from clig.dev."""
from importlib.metadata import version

import pytest

from docs2epub.cli import main


def test_bare_invocation_is_concise_successful_help(capsys):
  assert main([]) == 0
  out, err = capsys.readouterr()
  assert not err
  assert "Turn documentation sites" in out
  assert "docs2epub https://" in out
  assert "--help" in out
  assert len(out.splitlines()) < 20


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_precedes_other_invalid_arguments(flag, capsys):
  assert main(["--format", "invalid", "--unknown", flag]) == 0
  out, err = capsys.readouterr()
  assert not err
  assert "Examples:" in out
  assert "https://github.com/brenorb/docs2epub/issues" in out
  assert "--max-pages" in out


def test_version_matches_installed_distribution(capsys):
  assert main(["--version"]) == 0
  out, err = capsys.readouterr()
  assert out.strip() == f"docs2epub {version('docs2epub')}"
  assert not err


@pytest.mark.parametrize("args", [
  ["https://example.com"],
  ["not-a-url", "book.epub"],
  ["https://example.com", "book.epub", "--max-pages", "0"],
  ["https://example.com", "book.epub", "--sleep-s", "nan"],
  ["https://example.com", "book.epub", "--timeout", "0"],
  ["https://example.com", "book.epub", "--tim", "10"],
])
def test_invalid_input_fails_before_network(args, monkeypatch, capsys):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda *_: pytest.fail("invalid input reached network"))
  with pytest.raises(SystemExit) as exc:
    main(args)
  assert exc.value.code == 2
  out, err = capsys.readouterr()
  assert not out
  assert "error:" in err
  assert "Traceback" not in err


def test_configured_timeout_reaches_page_requests(monkeypatch):
  from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next

  calls = []
  class Response:
    text = "<article><h1>Intro</h1><p>Documentation.</p></article>"
    def raise_for_status(self):
      pass
  class Session:
    headers = {}
    def get(self, url, *, timeout):
      calls.append(timeout)
      return Response()
  monkeypatch.setattr("docs2epub.docusaurus_next.requests.Session", Session)
  iter_docusaurus_next(DocusaurusNextOptions(start_url="https://example.com/docs", sleep_s=0, timeout=7.5))
  assert calls == [7.5]
