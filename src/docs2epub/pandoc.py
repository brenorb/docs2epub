from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests
from platformdirs import user_cache_path


PANDOC_VERSION = "3.12.1"
# SHA-256 digests published on the official jgm/pandoc release assets.
_ARCHIVES = {
  ("Darwin", "arm64"): ("arm64-macOS.zip", "c2146cf33a583f3ac93eccddf1bb662371d5cfcce1aad1c87ad860cca1435d46"),
  ("Darwin", "x86_64"): ("x86_64-macOS.zip", "81ed3e2cfecf096df15d407152f89a684fd65221082b919963f738e977fad3bc"),
  ("Linux", "arm64"): ("linux-arm64.tar.gz", "445d96fd08801fe636cab1158b4f017ee320ac3b7446328b4fe2f902117b19b9"),
  ("Linux", "x86_64"): ("linux-amd64.tar.gz", "d0c90410e90204c9ca83b8539fac5c7aed01fd537207e4585849f8abc5df20b8"),
  ("Windows", "x86_64"): ("windows-x86_64.zip", "6ef431cb20b2c24a0371fc19200dc49d452be54b1b5c9239f3462841ef53e587"),
}


def _copy_binary(archive: Path, target: Path, binary_name: str) -> None:
  # Copy only the executable's bytes, never extract archive paths or links.
  if archive.name.endswith(".zip"):
    with zipfile.ZipFile(archive) as package:
      member = next(m for m in package.infolist() if Path(m.filename).name == binary_name and not m.is_dir())
      with package.open(member) as source, target.open("wb") as dest:
        shutil.copyfileobj(source, dest)
  else:
    with tarfile.open(archive, "r:gz") as package:
      member = next(m for m in package.getmembers() if Path(m.name).name == binary_name and m.isfile())
      source = package.extractfile(member)
      if source is None:
        raise ValueError("Pandoc archive has no executable")
      with source, target.open("wb") as dest:
        shutil.copyfileobj(source, dest)


def ensure_pandoc() -> str:
  installed = shutil.which("pandoc")
  if installed:
    return installed

  system = platform.system()
  machine = platform.machine().lower()
  arch = {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)
  asset = _ARCHIVES.get((system, arch))
  guidance = "Install pandoc (https://pandoc.org/installing.html) or use --format epub3."
  if asset is None:
    raise RuntimeError(f"Automatic Pandoc installation is unsupported on {system}/{machine}. {guidance}")

  suffix, checksum = asset
  filename = f"pandoc-{PANDOC_VERSION}-{suffix}"
  url = f"https://github.com/jgm/pandoc/releases/download/{PANDOC_VERSION}/{filename}"
  cache_override = os.environ.get("DOCS2EPUB_CACHE_DIR")
  cache_root = Path(cache_override).expanduser() if cache_override else user_cache_path("docs2epub")
  cache_dir = cache_root / "pandoc" / PANDOC_VERSION / f"{system}-{arch}"
  binary_name = "pandoc.exe" if system == "Windows" else "pandoc"
  binary = cache_dir / binary_name
  if binary.is_file() and os.access(binary, os.X_OK):
    return str(binary.resolve())

  print(f"Installing Pandoc {PANDOC_VERSION} for {system}/{arch}...", file=sys.stderr)
  try:
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Keep incomplete downloads out of the cache; publish only a tested binary.
    with tempfile.TemporaryDirectory(prefix="install-", dir=cache_dir) as tmp:
      archive = Path(tmp) / filename
      digest = hashlib.sha256()
      with requests.get(url, stream=True, timeout=(10, 120)) as response:
        response.raise_for_status()
        with archive.open("wb") as dest:
          for chunk in response.iter_content(chunk_size=1024 * 1024):
            digest.update(chunk)
            dest.write(chunk)
      if digest.hexdigest() != checksum:
        raise ValueError("Pandoc archive checksum mismatch")
      candidate = Path(tmp) / binary_name
      _copy_binary(archive, candidate, binary_name)
      candidate.chmod(0o755)
      subprocess.run([str(candidate), "--version"], check=True, capture_output=True, timeout=30)
      os.replace(candidate, binary)
  except (requests.RequestException, OSError, ValueError, tarfile.TarError,
          zipfile.BadZipFile, StopIteration, subprocess.SubprocessError) as exc:
    raise RuntimeError(f"Could not install Pandoc automatically: {exc}. {guidance}") from exc
  return str(binary.resolve())
