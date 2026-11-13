import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docs2epub.cli import main
from docs2epub.model import Chapter

legacy = bool(os.environ.get("DOCS2EPUB_LEGACY"))
def fail(*, out_file, **_options):
    out_file.write_bytes(b"incomplete")
    raise RuntimeError("fixture conversion failed")

with TemporaryDirectory() as directory:
    output = Path(directory) / "book.epub"
    output.write_bytes(b"original")
    with patch("docs2epub.cli.iter_docusaurus_next", return_value=[
        Chapter(index=1, title="Intro", url="https://docs.example.test/intro", html="<p>Intro</p>")
    ]), patch("docs2epub.cli.build_epub2_with_pandoc", side_effect=fail):
        try:
            main(["https://docs.example.test/intro", str(output)])
        except SystemExit as error:
            assert "fixture conversion failed" in str(error)
        else:
            raise AssertionError("Expected the writer to fail")
    assert output.read_bytes() == (b"incomplete" if legacy else b"original")
    assert list(output.parent.iterdir()) == [output]
print("Writer failure and destination bytes checked")
