from pathlib import Path

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
