from pathlib import Path

import pytest

from docs2epub.model import Chapter
from docs2epub.pandoc_epub2 import PandocEpub2Options, build_epub2_with_pandoc


def test_build_epub2_sets_resource_path_and_cwd(monkeypatch, tmp_path):
  monkeypatch.setattr("docs2epub.pandoc_epub2.shutil.which", lambda _: "/usr/bin/pandoc")

  captured: dict[str, object] = {}

  class Proc:
    returncode = 0
    stderr = ""
    stdout = ""

  def fake_run(cmd, **kwargs):
    captured["cmd"] = cmd
    captured["cwd"] = kwargs.get("cwd")
    return Proc()

  monkeypatch.setattr("docs2epub.pandoc_epub2.subprocess.run", fake_run)

  out_file = tmp_path / "out.epub"
  build_epub2_with_pandoc(
    chapters=[Chapter(index=1, title="One", url="https://example.com/docs", html="<p>body</p>")],
    out_file=out_file,
    title="Book",
    author="Author",
    language="en",
    publisher=None,
    identifier=None,
    verbose=False,
    options=PandocEpub2Options(),
  )

  cmd = captured["cmd"]
  cwd = captured["cwd"]

  assert isinstance(cmd, list)
  assert "--resource-path" in cmd
  idx = cmd.index("--resource-path")
  assert str(cwd) == cmd[idx + 1]
  assert any(str(part).startswith("chapter_") and str(part).endswith(".html") for part in cmd)


def test_build_epub2_uses_absolute_output_path(monkeypatch, tmp_path):
  monkeypatch.setattr("docs2epub.pandoc_epub2.shutil.which", lambda _: "/usr/bin/pandoc")

  captured: dict[str, object] = {}

  class Proc:
    returncode = 0
    stderr = ""
    stdout = ""

  def fake_run(cmd, **kwargs):
    captured["cmd"] = cmd
    captured["cwd"] = kwargs.get("cwd")
    return Proc()

  monkeypatch.setattr("docs2epub.pandoc_epub2.subprocess.run", fake_run)

  old_cwd = Path.cwd()
  try:
    import os

    os.chdir(tmp_path)
    build_epub2_with_pandoc(
      chapters=[Chapter(index=1, title="One", url="https://example.com/docs", html="<p>body</p>")],
      out_file="book.epub",
      title="Book",
      author="Author",
      language="en",
      publisher=None,
      identifier=None,
      verbose=False,
      options=PandocEpub2Options(),
    )
  finally:
    os.chdir(old_cwd)

  cmd = captured["cmd"]
  assert isinstance(cmd, list)
  out_idx = cmd.index("-o")
  assert cmd[out_idx + 1] == str((tmp_path / "book.epub").resolve())


def test_build_epub2_raises_when_pandoc_is_missing(monkeypatch, tmp_path):
  monkeypatch.setattr("docs2epub.pandoc_epub2.shutil.which", lambda _: None)

  with pytest.raises(RuntimeError, match="pandoc not found"):
    build_epub2_with_pandoc(
      chapters=[Chapter(index=1, title="One", url="https://example.com/docs", html="<p>body</p>")],
      out_file=tmp_path / "out.epub",
      title="Book",
      author="Author",
      language="en",
      publisher=None,
      identifier=None,
      verbose=False,
      options=PandocEpub2Options(),
    )


def test_build_epub2_summarizes_duplicate_and_missing_resource_warnings(monkeypatch, tmp_path, capsys):
  monkeypatch.setattr("docs2epub.pandoc_epub2.shutil.which", lambda _: "/usr/bin/pandoc")

  class Proc:
    returncode = 0
    stdout = ""
    stderr = "\n".join(
      [
        "[WARNING] Duplicate identifier: foo",
        "[WARNING] Duplicate identifier: bar",
        "[WARNING] Could not fetch resource https://example.com/a.png",
      ]
    )

  monkeypatch.setattr("docs2epub.pandoc_epub2.subprocess.run", lambda *args, **kwargs: Proc())

  out_file = tmp_path / "out.epub"
  build_epub2_with_pandoc(
    chapters=[Chapter(index=1, title="One", url="https://example.com/docs", html="<p>body</p>")],
    out_file=out_file,
    title="Book",
    author="Author",
    language="en",
    publisher=None,
    identifier=None,
    verbose=False,
    options=PandocEpub2Options(),
  )

  output = capsys.readouterr().out
  assert "pandoc warnings: 3" in output
  assert "Duplicate identifier: 2" in output
  assert "Missing resources: 1" in output
