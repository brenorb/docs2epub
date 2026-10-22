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


def stub_conversion(monkeypatch):
  from pathlib import Path
  from docs2epub.model import Chapter
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: [Chapter(index=1, title="Intro", url="https://example.com", html="<p>text</p>")])
  def build(**kwargs):
    output = Path(kwargs["out_file"])
    output.write_bytes(b"epub")
    return output
  monkeypatch.setattr("docs2epub.cli.build_epub2_with_pandoc", build)
  monkeypatch.setattr("docs2epub.cli.build_epub", build)


def test_json_result_is_clean_stdout_with_progress_on_stderr(monkeypatch, tmp_path, capsys):
  import json
  stub_conversion(monkeypatch)
  output = tmp_path / "book.epub"
  assert main(["https://example.com", str(output), "--json"]) == 0
  out, err = capsys.readouterr()
  assert json.loads(out) == {"ok": True, "output": str(output), "pages": 1, "size_bytes": 4, "format": "epub2"}
  assert "Scraping" in err
  assert "Writing" in err


def test_quiet_preserves_primary_result(monkeypatch, tmp_path, capsys):
  stub_conversion(monkeypatch)
  assert main(["https://example.com", str(tmp_path / "book.epub"), "-q"]) == 0
  out, err = capsys.readouterr()
  assert "EPUB written to:" in out
  assert not err


@pytest.mark.parametrize("format", ["epub2", "epub3"])
def test_failed_conversion_preserves_existing_output(monkeypatch, tmp_path, format):
  from pathlib import Path
  stub_conversion(monkeypatch)
  output = tmp_path / "book.epub"
  output.write_bytes(b"original book")
  def fail(**kwargs):
    Path(kwargs["out_file"]).write_bytes(b"incomplete book")
    raise OSError("disk full")
  monkeypatch.setattr("docs2epub.cli.build_epub2_with_pandoc", fail)
  monkeypatch.setattr("docs2epub.cli.build_epub", fail)
  with pytest.raises(SystemExit, match="disk full"):
    main(["https://example.com", str(output), "--format", format])
  assert output.read_bytes() == b"original book"
  assert list(tmp_path.iterdir()) == [output]


def test_ctrl_c_reports_interrupt_without_traceback(monkeypatch, tmp_path, capsys):
  def interrupt(_):
    raise KeyboardInterrupt
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", interrupt)
  assert main(["https://example.com", str(tmp_path / "book.epub")]) == 130
  out, err = capsys.readouterr()
  assert not out
  assert "Interrupted" in err


def test_network_error_is_actionable_and_suppresses_traceback(monkeypatch, tmp_path):
  import requests
  def timeout(_):
    raise requests.Timeout("server did not respond")
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", timeout)
  with pytest.raises(SystemExit, match="server did not respond") as exc:
    main(["https://example.com", str(tmp_path / "book.epub")])
  assert exc.value.__suppress_context__


def test_stdout_destination_contains_only_epub_bytes(monkeypatch, tmp_path, capsysbinary):
  stub_conversion(monkeypatch)
  monkeypatch.chdir(tmp_path)
  assert main(["https://example.com", "-"]) == 0
  out, err = capsysbinary.readouterr()
  assert out == b"epub"
  assert b"Scraping" in err
  assert list(tmp_path.iterdir()) == []


def test_binary_output_is_rejected_on_a_terminal_before_network(monkeypatch):
  monkeypatch.setattr("sys.stdout.isatty", lambda: True)
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: pytest.fail("should not scrape"))
  with pytest.raises(SystemExit) as exc:
    main(["https://example.com", "-"])
  assert exc.value.code == 2


def test_json_and_binary_stdout_are_mutually_exclusive(monkeypatch):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: pytest.fail("should not scrape"))
  with pytest.raises(SystemExit) as exc:
    main(["https://example.com", "-", "--json"])
  assert exc.value.code == 2


def test_dry_run_does_not_scrape_or_create_output(monkeypatch, tmp_path, capsys):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: pytest.fail("dry run should not scrape"))
  output = tmp_path / "new-dir" / "book.epub"
  assert main(["https://example.com", str(output), "--dry-run"]) == 0
  out, err = capsys.readouterr()
  assert "https://example.com" in out
  assert str(output) in out
  assert "Pandoc" in out
  assert not err
  assert not output.parent.exists()


@pytest.mark.parametrize("url", ["http://[broken", "https://example.com:bad-port/docs"])
def test_malformed_urls_are_usage_errors(url, monkeypatch, capsys):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: pytest.fail("invalid URL reached network"))
  with pytest.raises(SystemExit) as exc:
    main([url, "book.epub"])
  assert exc.value.code == 2
  assert "HTTP or HTTPS URL" in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--timeout", "--sleep-s"])
def test_extreme_durations_are_usage_errors_before_network(option, monkeypatch, capsys):
  monkeypatch.setattr("docs2epub.cli.iter_docusaurus_next", lambda _: pytest.fail("invalid duration reached network"))
  with pytest.raises(SystemExit) as exc:
    main(["https://example.com", "book.epub", option, "1e300"])
  assert exc.value.code == 2
  assert "86400" in capsys.readouterr().err


@pytest.mark.parametrize("args", [[], ["--help"], ["--version"]])
def test_information_commands_handle_closed_stdout(args):
  import subprocess
  import sys
  command = "import sys; from docs2epub.cli import main; sys.exit(main(" + repr(args) + "))"
  process = subprocess.Popen([sys.executable, "-c", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  process.stdout.close()
  assert process.wait(timeout=10) == 0
  assert process.stderr.read() == b""
