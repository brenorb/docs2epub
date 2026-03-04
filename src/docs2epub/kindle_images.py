from __future__ import annotations

import hashlib
import io
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image, UnidentifiedImageError


def _svg_to_png_bytes(raw_svg: bytes) -> bytes:
  import cairosvg

  return cairosvg.svg2png(bytestring=raw_svg)


def _to_kindle_image(raw: bytes, *, media_type: str, ext_hint: str) -> tuple[bytes, str]:
  media_type = media_type.lower()
  ext_hint = ext_hint.lower()

  if media_type == "image/svg+xml" or ext_hint == ".svg":
    return _svg_to_png_bytes(raw), ".png"

  if media_type == "image/gif" or ext_hint == ".gif":
    return raw, ".gif"

  try:
    with Image.open(io.BytesIO(raw)) as image:
      image.load()
      # Kindle accepts PNG/JPEG/GIF. Normalize everything else to PNG.
      with io.BytesIO() as converted:
        image.save(converted, format="PNG")
        return converted.getvalue(), ".png"
  except (UnidentifiedImageError, OSError) as exc:
    raise ValueError("unsupported image content") from exc


class KindleImageProcessor:
  def __init__(
    self,
    *,
    assets_dir: Path,
    session: requests.Session | None = None,
    timeout_s: int = 30,
  ) -> None:
    self.assets_dir = Path(assets_dir)
    self.assets_dir.mkdir(parents=True, exist_ok=True)
    self._session = session or requests.Session()
    self._timeout_s = timeout_s
    self._cache: dict[str, str | None] = {}

  def rewrite(self, src: str, base_url: str) -> str | None:
    raw_src = src.strip()
    if not raw_src:
      return None
    if raw_src.startswith(("data:", "cid:")):
      return None

    abs_url = urljoin(base_url, raw_src)
    parsed = urlparse(abs_url)
    if parsed.scheme not in {"http", "https"}:
      return None

    cached = self._cache.get(abs_url)
    if cached is not None:
      return cached

    rel = self._download_and_convert(abs_url)
    self._cache[abs_url] = rel
    return rel

  def _download_and_convert(self, abs_url: str) -> str | None:
    try:
      response = self._session.get(abs_url, timeout=self._timeout_s)
      response.raise_for_status()
    except requests.RequestException:
      return None

    media_type = str(response.headers.get("content-type") or "").split(";", 1)[0].strip()
    ext_hint = Path(urlparse(abs_url).path).suffix

    try:
      converted, suffix = _to_kindle_image(response.content, media_type=media_type, ext_hint=ext_hint)
    except Exception:
      return None

    digest = hashlib.sha256(abs_url.encode("utf-8")).hexdigest()[:16]
    name = f"img-{digest}{suffix}"
    out_file = self.assets_dir / name
    if not out_file.exists():
      out_file.write_bytes(converted)
    return f"{self.assets_dir.name}/{name}"
