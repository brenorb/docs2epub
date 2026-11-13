import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import requests
from docs2epub.kindle_images import KindleImageProcessor
from PIL import Image

buffer = io.BytesIO()
Image.new("RGB", (1, 1)).save(buffer, format="PNG")
def response(status):
    result = requests.Response()
    result.status_code = status
    result.headers["content-type"] = "image/png"
    result._content = buffer.getvalue()
    return result

with TemporaryDirectory() as directory:
    for outcomes in ((404, 404), (404, 200), (200,)):
        session = Mock()
        session.get.side_effect = [response(status) for status in outcomes]
        processor = KindleImageProcessor(assets_dir=Path(directory) / "assets", session=session)
        results = [processor.rewrite("image.png", "https://docs.example.test/") for _ in range(2)]
        assert bool(results[0]) == (outcomes[0] == 200)
        assert bool(results[1]) == (outcomes[-1] == 200)
        assert session.get.call_count == len(outcomes)
print("Successful image reuse and failed image retry checked")
