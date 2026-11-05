"""Exercise an installed CLI against a real loopback documentation server.

Run with uv run python scripts/e2e_cli.py /path/to/installed/docs2epub.
EPUB2 uses a real Pandoc executable (including the normal cached installer).
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from posixpath import dirname, join, normpath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


def png() -> bytes:
  def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
  return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
          + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\x00\xff\x00")) + chunk(b"IEND", b""))


class Documentation(BaseHTTPRequestHandler):
  requests = 0

  def do_GET(self):
    type(self).requests += 1
    if self.path == "/slow":
      time.sleep(0.2)
    if self.path not in {"/docs/intro", "/docs/next", "/pixel.png"}:
      self.send_error(503, "E2E fixture unavailable")
      return
    if self.path == "/pixel.png":
      content, kind = png(), "image/png"
    else:
      marker = "E2E_INTRO" if self.path.endswith("intro") else "E2E_NEXT"
      content = (f'<html><aside class="sidebar"><a href="/docs/intro">Intro</a>'
                 f'<a href="/docs/next">Next</a></aside><article><h1 id="title">{marker}</h1>'
                 f'<p>{marker}_CONTENT</p><h2 id="target">Details</h2>'
                 '<a href="#target">Stay in this chapter</a>'
                 '<a href="/docs/next#target">Continue inside the book</a>'
                 '<a href="/docs/next#title">Jump to the next title</a>'
                 '<img src="/pixel.png" alt="E2E image"></article></html>').encode()
      kind = "text/html"
    self.send_response(200)
    self.send_header("Content-Type", kind)
    self.send_header("Content-Length", str(len(content)))
    self.end_headers()
    try:
      self.wfile.write(content)
    except BrokenPipeError:
      pass

  def log_message(self, *_args):
    pass


def verify_book(data: bytes):
  with zipfile.ZipFile(io.BytesIO(data)) as book:
    assert book.read("mimetype") == b"application/epub+zip"
    assert "META-INF/container.xml" in book.namelist()
    assert any(name.endswith(".opf") for name in book.namelist())
    assert any(name.endswith(".png") for name in book.namelist()), book.namelist()
    documents = {name: book.read(name) for name in book.namelist() if name.endswith((".html", ".xhtml"))}
    chapters = {}
    for marker in (b"E2E_INTRO_CONTENT", b"E2E_NEXT_CONTENT"):
      matches = [name for name, content in documents.items() if marker in content]
      assert len(matches) == 1, (marker, matches)
      chapters[matches[0]] = ElementTree.fromstring(documents[matches[0]])
    intro_path, next_path = chapters
    for source in (intro_path, next_path):
      expected = {
        "Stay in this chapter": source,
        "Continue inside the book": next_path,
        "Jump to the next title": next_path,
      }
      for label, destination in expected.items():
        anchors = [a for a in chapters[source].findall(".//{*}a") if "".join(a.itertext()) == label]
        assert len(anchors) == 1, (source, label)
        href = urlsplit(anchors[0].get("href", ""))
        assert not href.scheme and not href.netloc and href.fragment, (source, label, href)
        target = normpath(join(dirname(source), unquote(href.path))) if href.path else source
        assert target == destination, (source, label, target, destination)
        fragment = unquote(href.fragment)
        assert sum(el.get("id") == fragment for el in chapters[target].iter()) == 1, (target, fragment)


def main() -> int:
  cli = str(Path(sys.argv[1]).resolve()) if len(sys.argv) > 1 else str(Path(sys.executable).with_name("docs2epub"))
  server = ThreadingHTTPServer(("127.0.0.1", 0), Documentation)
  server.daemon_threads = True
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()
  origin = f"http://127.0.0.1:{server.server_port}"

  def run(*args, expected=0):
    result = subprocess.run([cli, *map(str, args)], capture_output=True, timeout=180)
    assert result.returncode == expected, result.stderr.decode(errors="replace")
    assert b"Traceback" not in result.stderr
    return result

  try:
    with tempfile.TemporaryDirectory(prefix="docs2epub-e2e-") as temporary:
      root = Path(temporary)
      for format in ("epub2", "epub3"):
        output = root / f"book-{format}.epub"
        result = run(f"{origin}/docs/intro", output, "--format", format, "--sleep-s", 0, "--json")
        summary = json.loads(result.stdout)
        assert summary["pages"] == 2 and summary["output"] == str(output.resolve()), summary
        assert summary["size_bytes"] == output.stat().st_size
        verify_book(output.read_bytes())
      streamed = run(f"{origin}/docs/intro", "-", "--format", "epub3", "--sleep-s", 0, "--quiet")
      verify_book(streamed.stdout)
      assert streamed.stderr == b""

      count = Documentation.requests
      planned = root / "not-created" / "plan.epub"
      run(f"{origin}/docs/intro", planned, "--dry-run", "--json")
      assert not planned.parent.exists() and Documentation.requests == count

      existing = root / "book-epub3.epub"
      digest = hashlib.sha256(existing.read_bytes()).digest()
      run(f"{origin}/fail", existing, "--format", "epub3", expected=1)
      run(f"{origin}/slow", existing, "--format", "epub3", "--timeout", "0.02", expected=1)
      assert hashlib.sha256(existing.read_bytes()).digest() == digest
      assert not list(root.glob(".docs2epub-*"))

      help_process = subprocess.Popen([cli, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      help_process.stdout.close()
      assert help_process.wait(timeout=10) == 0
      assert help_process.stderr.read() == b""
      print("E2E passed: installed CLI, real HTTP scrape, native EPUB2/EPUB3, embedded images/links, JSON, binary pipe, dry run, timeout/error recovery, closed help pipe.")
  finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
