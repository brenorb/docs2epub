import hashlib
import io
import subprocess
import tarfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from docs2epub import pandoc


@pytest.fixture
def install_env(monkeypatch, tmp_path):
  monkeypatch.setattr(pandoc.shutil, "which", lambda _: None)
  monkeypatch.setenv("DOCS2EPUB_CACHE_DIR", str(tmp_path))
  monkeypatch.setattr(pandoc.platform, "system", lambda: "Darwin")
  monkeypatch.setattr(pandoc.platform, "machine", lambda: "arm64")
  return tmp_path


def _archive_bytes(filename, binary_name="pandoc"):
  buffer = io.BytesIO()
  if filename.endswith(".zip"):
    with zipfile.ZipFile(buffer, "w") as archive:
      archive.writestr(f"pandoc/bin/{binary_name}", b"native pandoc")
      archive.writestr("../../unexpected-file", b"do not extract")
  else:
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
      member = tarfile.TarInfo(f"pandoc/bin/{binary_name}")
      member.size = len(b"native pandoc")
      archive.addfile(member, io.BytesIO(b"native pandoc"))
  return buffer.getvalue()


def test_system_pandoc_needs_no_download(monkeypatch, tmp_path):
  monkeypatch.setattr(pandoc.shutil, "which", lambda _: "/usr/bin/pandoc")
  monkeypatch.setattr(pandoc.requests, "get", lambda *a, **kw: pytest.fail("unexpected download"))
  assert pandoc.ensure_pandoc() == "/usr/bin/pandoc"


@pytest.mark.parametrize("system,machine,arch", [
  ("Darwin", "arm64", "arm64"),
  ("Darwin", "x86_64", "x86_64"),
  ("Linux", "aarch64", "arm64"),
  ("Linux", "x86_64", "x86_64"),
  ("Windows", "AMD64", "x86_64"),
])
@pytest.mark.parametrize("executable_works", [True, False])
def test_install_native_archive_and_reuse_cache(install_env, monkeypatch, system, machine, arch, executable_works):
  monkeypatch.setattr(pandoc.platform, "system", lambda: system)
  monkeypatch.setattr(pandoc.platform, "machine", lambda: machine)
  suffix, _ = pandoc._ARCHIVES[(system, arch)]
  binary_name = "pandoc.exe" if system == "Windows" else "pandoc"
  data = _archive_bytes(suffix, binary_name)
  monkeypatch.setitem(pandoc._ARCHIVES, (system, arch), (suffix, hashlib.sha256(data).hexdigest()))
  urls = []
  commands = []

  class Response:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      pass

    def raise_for_status(self):
      pass

    def iter_content(self, **kwargs):
      yield data

  def fake_get(url, **kwargs):
    urls.append(url)
    assert kwargs["stream"] is True
    assert kwargs["timeout"] == (10, 120)
    return Response()

  def fake_run(cmd, **kwargs):
    commands.append(cmd)
    assert Path(cmd[0]).read_bytes() == b"native pandoc"
    assert kwargs["check"] is True
    if not executable_works:
      raise subprocess.CalledProcessError(1, cmd)
    return SimpleNamespace(returncode=0)

  monkeypatch.setattr(pandoc.requests, "get", fake_get)
  monkeypatch.setattr(pandoc.subprocess, "run", fake_run)
  if not executable_works:
    with pytest.raises(RuntimeError, match="Could not install Pandoc automatically"):
      pandoc.ensure_pandoc()
    assert not [p for p in install_env.rglob(binary_name) if p.is_file()]
    assert not list(install_env.rglob("install-*"))
    return
  result = Path(pandoc.ensure_pandoc())
  assert result.name == binary_name
  assert result.read_bytes() == b"native pandoc"
  assert result.stat().st_mode & 0o111
  assert urls == [f"https://github.com/jgm/pandoc/releases/download/{pandoc.PANDOC_VERSION}/pandoc-{pandoc.PANDOC_VERSION}-{suffix}"]
  assert commands[0][1:] == ["--version"]
  assert pandoc.ensure_pandoc() == str(result)
  assert len(urls) == len(commands) == 1
  assert list(result.parent.iterdir()) == [result]
  assert not (install_env / "unexpected-file").exists()


def test_download_failure_is_actionable_and_not_cached(install_env, monkeypatch):
  def fail_download(*args, **kwargs):
    raise requests.ConnectionError("offline")

  monkeypatch.setattr(pandoc.requests, "get", fail_download)
  with pytest.raises(RuntimeError, match="offline.*--format epub3"):
    pandoc.ensure_pandoc()
  assert not list(install_env.rglob("install-*"))
  assert not [p for p in install_env.rglob("pandoc") if p.is_file()]


def test_checksum_failure_never_executes_download(install_env, monkeypatch):
  class Response:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      pass

    def raise_for_status(self):
      pass

    def iter_content(self, **kwargs):
      yield b"bad archive"

  monkeypatch.setattr(pandoc.requests, "get", lambda *a, **kw: Response())
  monkeypatch.setattr(pandoc.subprocess, "run", lambda *a, **kw: pytest.fail("unexpected execution"))
  with pytest.raises(RuntimeError, match="checksum mismatch"):
    pandoc.ensure_pandoc()
  assert not list(install_env.rglob("install-*"))


def test_unsupported_platform_needs_no_download(install_env, monkeypatch):
  monkeypatch.setattr(pandoc.platform, "machine", lambda: "riscv64")
  monkeypatch.setattr(pandoc.requests, "get", lambda *a, **kw: pytest.fail("unexpected download"))
  with pytest.raises(RuntimeError, match="unsupported.*riscv64.*--format epub3"):
    pandoc.ensure_pandoc()
