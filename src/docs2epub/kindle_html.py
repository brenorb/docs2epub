from __future__ import annotations

import re

from bs4 import BeautifulSoup


def clean_html_for_kindle_epub2(
  html_fragment: str,
  *,
  keep_images: bool,
) -> str:
  """Best-effort HTML cleanup for Kindle-friendly EPUB2.

  This is intentionally conservative: it strips known-problematic attributes
  and tags that commonly cause Send-to-Kindle conversion issues.

  By default we drop remote images to avoid pandoc fetch failures.
  """

  soup = BeautifulSoup(html_fragment, "lxml")

  if not keep_images:
    for img in list(soup.find_all("img")):
      src = str(img.get("src") or "")
      if src.startswith("http://") or src.startswith("https://"):
        img.decompose()

  # EPUB2: <u> tag isn't consistently supported; convert to a span.
  for u in list(soup.find_all("u")):
    span = soup.new_tag("span")
    span["style"] = "text-decoration: underline;"
    if u.string is None:
      for child in list(u.contents):
        span.append(child)
    else:
      span.string = u.string
    u.replace_with(span)

  # Remove tabindex attributes (not allowed in EPUB2 XHTML).
  for el in soup.find_all(attrs={"tabindex": True}):
    el.attrs.pop("tabindex", None)

  # Remove start attribute from ordered lists (not allowed in EPUB2 XHTML).
  for ol in soup.find_all("ol"):
    ol.attrs.pop("start", None)

  # Strip duplicate ids in a simple way: if an id repeats, rename it.
  seen_ids: set[str] = set()
  for el in soup.find_all(attrs={"id": True}):
    raw = str(el.get("id") or "").strip()
    if not raw:
      continue
    if raw not in seen_ids:
      seen_ids.add(raw)
      continue
    suffix = 2
    new_id = f"{raw}-{suffix}"
    while new_id in seen_ids:
      suffix += 1
      new_id = f"{raw}-{suffix}"
    el["id"] = new_id
    seen_ids.add(new_id)

  # If href="#something" but no element has id="something", drop href.
  all_ids = {str(el.get("id")) for el in soup.find_all(attrs={"id": True})}
  for a in soup.find_all("a", href=True):
    href = str(a.get("href") or "")
    if href.startswith("#") and len(href) > 1:
      frag = href[1:]
      if frag not in all_ids:
        a.attrs.pop("href", None)

  # Normalize whitespace a bit (helps keep diffs smaller and reduces odd output).
  text = str(soup)
  text = re.sub(r"\s+", " ", text)
  return text.strip()
