import configparser
import subprocess
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

workflow = Path(".github/workflows/publish.yml").read_text()
assert '      - "v*"' in workflow
assert workflow.index("run: uv build") < workflow.index("run: uv publish")
with TemporaryDirectory() as directory:
    subprocess.run(["uv", "build", "--out-dir", directory], check=True)
    root = Path(directory)
    assert len(list(root.glob("*.tar.gz"))) == 1
    wheel, = root.glob("*.whl")
    with zipfile.ZipFile(wheel) as package:
        metadata, = (name for name in package.namelist() if name.endswith("/entry_points.txt"))
        parser = configparser.ConfigParser()
        parser.read_string(package.read(metadata).decode())
        assert dict(parser["console_scripts"]) == {"docs2epub": "docs2epub.cli:main"}
        assert "docs2epub/cli.py" in package.namelist()
print("Tagged workflow and built wheel entrypoint checked")
