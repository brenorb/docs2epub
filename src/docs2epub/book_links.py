from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def canonicalize_book_url(url: str) -> str:
  parsed = urlparse(url)
  path = parsed.path or "/"
  if path != "/" and path.endswith("/"):
    path = path.rstrip("/")
  return parsed._replace(
    scheme=parsed.scheme.lower(),
    netloc=parsed.netloc.lower(),
    path=path,
    query="",
    fragment="",
  ).geturl()


def rewrite_internal_book_links(
  html_fragment: str,
  *,
  current_url: str,
  chapter_file_by_url: dict[str, str],
) -> str:
  soup = BeautifulSoup(html_fragment, "lxml")
  current_key = canonicalize_book_url(current_url)
  current_book_href = chapter_file_by_url.get(current_key)

  for anchor in soup.find_all("a", href=True):
    raw_href = str(anchor.get("href") or "").strip()
    if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
      continue

    abs_url = urljoin(current_url, raw_href)
    parsed = urlparse(abs_url)
    if parsed.scheme not in {"http", "https"}:
      continue

    target_key = canonicalize_book_url(abs_url)
    target_book_href = chapter_file_by_url.get(target_key)
    if not target_book_href:
      continue

    if target_book_href == current_book_href and parsed.fragment:
      anchor["href"] = f"#{parsed.fragment}"
      continue

    if parsed.fragment:
      anchor["href"] = f"{target_book_href}#{parsed.fragment}"
      continue

    anchor["href"] = target_book_href

  if soup.body is not None:
    return soup.body.decode_contents().strip()
  return str(soup).strip()
