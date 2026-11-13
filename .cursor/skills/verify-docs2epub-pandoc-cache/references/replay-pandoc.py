import hashlib
import io
import subprocess
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from docs2epub import pandoc

buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w") as archive:
    archive.writestr("pandoc-fixture/pandoc", b"local fixture executable")
data = buffer.getvalue()
response = Mock()
response.__enter__ = Mock(return_value=response)
response.__exit__ = Mock(return_value=False)
response.iter_content.return_value = iter([data])
with TemporaryDirectory() as directory:
    with (
        patch.dict("os.environ", {"DOCS2EPUB_CACHE_DIR": directory}),
        patch.object(pandoc.shutil, "which", return_value=None),
        patch.object(pandoc.platform, "system", return_value="Darwin"),
        patch.object(pandoc.platform, "machine", return_value="arm64"),
        patch.dict(pandoc._ARCHIVES, {("Darwin", "arm64"): ("fixture.zip", hashlib.sha256(data).hexdigest())}),
        patch.object(pandoc.requests, "get", return_value=response),
        patch.object(pandoc.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "pandoc")),
    ):
        try:
            pandoc.ensure_pandoc()
        except RuntimeError as error:
            assert "Could not install Pandoc automatically" in str(error)
        else:
            raise AssertionError("Expected the version probe failure to prevent publication")
    assert not any(path.is_file() for path in Path(directory).rglob("pandoc"))
    assert not list(Path(directory).rglob("install-*"))
print("Failed version probe leaves no cached executable")
