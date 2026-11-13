import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

runner = Path(sys.argv[1] if len(sys.argv) > 1 else "scripts/e2e_cli.py")
spec = importlib.util.spec_from_file_location("docs2epub_e2e", runner)
e2e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e2e)

archive = io.BytesIO()
with zipfile.ZipFile(archive, "w") as package:
    package.writestr("mimetype", "application/epub+zip")
    package.writestr("META-INF/container.xml", "")
    package.writestr("content.opf", "")
    package.writestr("page.xhtml", "E2E_INTRO_CONTENT E2E_NEXT_CONTENT")
    package.writestr("image.png", "")
book = archive.getvalue()

def run(args, **_options):
    url, destination, *flags = args[1:]
    output = Path(destination)
    if url.endswith("/fail"):
        output.write_bytes(b"unexpected replacement")
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")
    if url.endswith("/slow"):
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")
    if "--dry-run" in flags:
        return SimpleNamespace(returncode=0, stdout=b"{}", stderr=b"")
    if destination == "-":
        return SimpleNamespace(returncode=0, stdout=book, stderr=b"")
    output.write_bytes(book)
    summary = {"pages": 2, "output": str(output.resolve()), "size_bytes": len(book)}
    return SimpleNamespace(returncode=0, stdout=json.dumps(summary).encode(), stderr=b"")

def popen(*_args, **_options):
    raise RuntimeError("runner reached the closed-pipe check despite a changed digest")

with patch.object(e2e.subprocess, "run", side_effect=run), patch.object(e2e.subprocess, "Popen", side_effect=popen):
    try:
        e2e.main()
    except AssertionError:
        pass
    else:
        raise AssertionError("Expected the runner to reject changed bytes")
print("Acceptance runner rejected a changed destination digest")
