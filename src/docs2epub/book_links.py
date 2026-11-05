from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag


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
    if not raw_href or raw_href.startswith(("mailto:", "tel:", "javascript:")):
      continue
    if raw_href.startswith("#") and not (current_book_href or "").startswith("#"):
      continue

    abs_url = urljoin(current_url, raw_href)
    parsed = urlparse(abs_url)
    if parsed.scheme not in {"http", "https"}:
      continue

    target_key = canonicalize_book_url(abs_url)
    target_book_href = chapter_file_by_url.get(target_key)
    if not target_book_href:
      continue

    # Pandoc combines its inputs, then splits the EPUB into new filenames.
    # Global chapter anchors survive that split; input-file links do not.
    if target_book_href.startswith("#"):
      anchor["href"] = target_book_href + (f"-{parsed.fragment}" if parsed.fragment else "")
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


def remove_heading_keep_anchor(heading: Tag) -> None:
  """Remove duplicate title text without invalidating incoming fragment links."""
  anchor_id = heading.get("id")
  if anchor_id:
    heading.name = "span"
    heading.clear()
    heading.attrs = {"id": anchor_id}
  else:
    heading.decompose()


def namespace_html_ids(html_fragment: str, prefix: str) -> str:
  """Give combined Pandoc inputs disjoint anchor namespaces."""
  soup = BeautifulSoup(html_fragment, "lxml")
  for el in soup.find_all(attrs={"id": True}):
    el["id"] = f"{prefix}-{el['id']}"
  return soup.body.decode_contents() if soup.body is not None else str(soup)
