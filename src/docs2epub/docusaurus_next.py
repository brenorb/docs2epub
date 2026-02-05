from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .model import Chapter


DEFAULT_USER_AGENT = "docs2epub/0.1 (+https://github.com/brenorb/docs2epub)"

_SIDEBAR_SELECTORS = [
  'aside[data-testid="table-of-contents"]',
  "aside#table-of-contents",
  'nav[aria-label="Table of contents"]',
  'nav[aria-label="Table of Contents"]',
  'nav[aria-label="Docs sidebar"]',
  'nav[aria-label="Docs navigation"]',
  'nav[aria-label="Documentation"]',
  'nav[aria-label="Docs"]',
  "aside.theme-doc-sidebar-container",
  "div.theme-doc-sidebar-container",
  "nav.theme-doc-sidebar-menu",
  "nav.menu",
  'nav[class*="menu"]',
  'aside[class*="sidebar"]',
  'nav[class*="sidebar"]',
]

_NON_DOC_EXTENSIONS = {
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".svg",
  ".webp",
  ".css",
  ".js",
  ".map",
  ".json",
  ".xml",
  ".rss",
  ".pdf",
  ".zip",
  ".tar",
  ".gz",
  ".tgz",
  ".epub",
  ".mp4",
  ".mp3",
  ".wav",
}


@dataclass(frozen=True)
class DocusaurusNextOptions:
  start_url: str
  base_url: str | None = None
  max_pages: int | None = None
  sleep_s: float = 0.5
  user_agent: str = DEFAULT_USER_AGENT


def _slugify_filename(text: str) -> str:
  value = text.strip().lower()
  value = re.sub(r"[^\w\s-]", "", value)
  value = re.sub(r"[\s_-]+", "-", value)
  value = value.strip("-")
  return value or "chapter"


def _extract_article(soup: BeautifulSoup) -> Tag:
  article = soup.find("article")
  if article:
    return article
  main = soup.find("main")
  if main:
    article = main.find("article")
    if article:
      return article
    return main
  role_main = soup.find(attrs={"role": "main"})
  if role_main:
    return role_main
  for selector in [
    "div#content",
    "div.content",
    "div#main",
    "div.main",
    "div#page",
    "div.page",
    "div.document",
    "div#document",
  ]:
    candidate = soup.select_one(selector)
    if candidate:
      return candidate
  body = soup.find("body")
  if body:
    return body
  raise RuntimeError("Could not find <article> in page HTML")


def _extract_canonical_url(soup: BeautifulSoup, *, base_url: str) -> str | None:
  for link in soup.find_all("link", href=True, rel=True):
    rel = link.get("rel")
    rel_values = []
    if isinstance(rel, list):
      rel_values = [str(r).lower() for r in rel]
    else:
      rel_values = [str(rel).lower()]
    if "canonical" not in rel_values:
      continue
    href = str(link.get("href") or "").strip()
    if not href:
      continue
    canonical = urljoin(base_url, href)
    parsed = urlparse(canonical)
    if parsed.scheme not in ("http", "https"):
      continue
    return canonical
  return None


def _canonicalize_url(url: str) -> str:
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


def _infer_root_path(start_url: str) -> str:
  parsed = urlparse(start_url)
  path = (parsed.path or "").rstrip("/")
  if not path:
    return ""
  parts = path.split("/")
  if len(parts) <= 2:
    return path
  return "/".join(parts[:-1])


def _path_within_root(path: str, root_path: str) -> bool:
  if not root_path or root_path == "/":
    return True
  if path == root_path:
    return True
  root = root_path if root_path.endswith("/") else f"{root_path}/"
  return path.startswith(root)


def _is_probable_doc_link(url: str) -> bool:
  parsed = urlparse(url)
  path = (parsed.path or "").lower()
  for ext in _NON_DOC_EXTENSIONS:
    if path.endswith(ext):
      return False
  return True


def _sidebar_candidates(soup: BeautifulSoup) -> list[Tag]:
  seen: set[int] = set()
  candidates: list[Tag] = []

  for selector in _SIDEBAR_SELECTORS:
    for el in soup.select(selector):
      key = id(el)
      if key in seen:
        continue
      seen.add(key)
      candidates.append(el)

  keywords = ["sidebar", "toc", "table of contents", "table-of-contents", "docs", "documentation"]
  for el in soup.find_all(["nav", "aside", "div"]):
    key = id(el)
    if key in seen:
      continue
    label = str(el.get("aria-label") or "").lower()
    elem_id = str(el.get("id") or "").lower()
    data_testid = str(el.get("data-testid") or "").lower()
    classes = " ".join(el.get("class", [])).lower()
    haystack = " ".join([label, elem_id, data_testid, classes])
    if any(k in haystack for k in keywords):
      seen.add(key)
      candidates.append(el)

  return candidates


def _looks_like_pager(container: Tag, links: list[Tag]) -> bool:
  label = str(container.get("aria-label") or "").lower()
  if "docs pages" in label or "breadcrumb" in label:
    return True
  if not links:
    return True
  texts = []
  for a in links:
    text = " ".join(a.get_text(" ", strip=True).split()).lower()
    if text:
      texts.append(text)
  if not texts:
    return False
  pager_words = {"next", "previous", "prev", "back"}
  return all(text in pager_words for text in texts)


def _extract_sidebar_urls(
  soup: BeautifulSoup,
  *,
  base_url: str,
  start_url: str,
) -> list[str]:
  candidates = _sidebar_candidates(soup)
  if not candidates:
    return []

  origin = urlparse(start_url).netloc.lower()
  root_path = _infer_root_path(start_url)
  best: list[str] = []
  for container in candidates:
    anchors = list(container.find_all("a", href=True))
    if _looks_like_pager(container, anchors):
      continue

    urls: list[str] = []
    seen: set[str] = set()
    for a in anchors:
      href = str(a.get("href") or "").strip()
      if not href or href.startswith("#"):
        continue
      if href.startswith(("mailto:", "tel:", "javascript:")):
        continue
      abs_url = urljoin(base_url, href)
      parsed = urlparse(abs_url)
      if parsed.scheme not in ("http", "https"):
        continue
      if origin and parsed.netloc.lower() != origin:
        continue
      if not _is_probable_doc_link(abs_url):
        continue
      if not _path_within_root(parsed.path or "", root_path):
        continue
      canonical = _canonicalize_url(abs_url)
      if canonical in seen:
        continue
      seen.add(canonical)
      urls.append(canonical)

    if len(urls) > len(best):
      best = urls

  return best


def _extract_content_urls(
  container: Tag,
  *,
  base_url: str,
  start_url: str,
) -> list[str]:
  origin = urlparse(start_url).netloc.lower()
  root_path = _infer_root_path(start_url)
  urls: list[str] = []
  seen: set[str] = set()

  for a in container.find_all("a", href=True):
    href = str(a.get("href") or "").strip()
    if not href or href.startswith("#"):
      continue
    if href.startswith(("mailto:", "tel:", "javascript:")):
      continue
    abs_url = urljoin(base_url, href)
    parsed = urlparse(abs_url)
    if parsed.scheme not in ("http", "https"):
      continue
    if origin and parsed.netloc.lower() != origin:
      continue
    if not _is_probable_doc_link(abs_url):
      continue
    if not _path_within_root(parsed.path or "", root_path):
      continue
    canonical = _canonicalize_url(abs_url)
    if canonical in seen:
      continue
    seen.add(canonical)
    urls.append(canonical)

  return urls


def _remove_unwanted(article: Tag) -> None:
  for selector in [
    'nav[aria-label="Breadcrumbs"]',
    'nav[aria-label="Breadcrumb"]',
    'nav[aria-label="Docs pages"]',
    "div.theme-doc-footer",
    "div.theme-doc-footer-edit-meta-row",
    "div.theme-doc-version-badge",
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "button",
  ]:
    for el in list(article.select(selector)):
      el.decompose()


def _absolutize_urls(container: Tag, base_url: str) -> None:
  for el in container.find_all(True):
    if el.has_attr("href"):
      href = str(el.get("href") or "")
      if href.startswith("/"):
        el["href"] = urljoin(base_url, href)
    if el.has_attr("src"):
      src = str(el.get("src") or "")
      if src.startswith("/"):
        el["src"] = urljoin(base_url, src)


def _extract_next_url(soup: BeautifulSoup, base_url: str) -> str | None:
  nav = soup.select_one('nav[aria-label="Docs pages"]')
  if not nav:
    return None

  for a in nav.find_all("a", href=True):
    text = " ".join(a.get_text(" ", strip=True).split())
    if text.lower().startswith("next"):
      return urljoin(base_url, a["href"])

  return None


def iter_docusaurus_next(options: DocusaurusNextOptions) -> list[Chapter]:
  session = requests.Session()
  session.headers.update({"User-Agent": options.user_agent})

  url = options.start_url
  base_url = options.base_url or options.start_url

  visited: set[str] = set()
  chapters: list[Chapter] = []

  def fetch_soup(target_url: str) -> BeautifulSoup:
    resp = session.get(target_url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")

  initial_soup = fetch_soup(url)
  canonical = _extract_canonical_url(initial_soup, base_url=url)
  if options.base_url is None and canonical:
    start_origin = urlparse(url).netloc.lower()
    canonical_origin = urlparse(canonical).netloc.lower()
    if canonical_origin == start_origin:
      canonical_key = _canonicalize_url(canonical)
      if canonical_key != _canonicalize_url(url):
        url = canonical
        base_url = canonical
        initial_soup = fetch_soup(url)

  sidebar_urls = _extract_sidebar_urls(initial_soup, base_url=base_url, start_url=url)
  initial_key = _canonicalize_url(url)

  def consume_page(target_url: str, *, soup: BeautifulSoup | None = None) -> Tag | None:
    if options.max_pages is not None and len(chapters) >= options.max_pages:
      return None
    key = _canonicalize_url(target_url)
    if key in visited:
      return None
    visited.add(key)

    page_soup = soup
    if page_soup is None:
      try:
        page_soup = fetch_soup(target_url)
      except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in {404, 410} and key != initial_key:
          return None
        raise

    try:
      article = _extract_article(page_soup)
    except RuntimeError:
      if key != initial_key:
        return None
      raise
    title_el = article.find(["h1", "h2"])
    title = (
      " ".join(title_el.get_text(" ", strip=True).split())
      if title_el
      else f"Chapter {len(chapters) + 1}"
    )
    if title_el is None and article.name == "body":
      body_text = " ".join(article.get_text(" ", strip=True).split())
      if len(body_text) < 200:
        return None

    _remove_unwanted(article)
    _absolutize_urls(article, base_url=target_url)

    for a in list(article.select('a.hash-link[href^="#"]')):
      a.decompose()

    html = article.decode_contents()
    chapters.append(Chapter(index=len(chapters) + 1, title=title, url=target_url, html=html))

    if options.sleep_s > 0 and (options.max_pages is None or len(chapters) < options.max_pages):
      import time

      time.sleep(options.sleep_s)

    return article

  if sidebar_urls:
    if initial_key not in {_canonicalize_url(u) for u in sidebar_urls}:
      sidebar_urls.insert(0, url)
    queue = list(sidebar_urls)
    discovered = {_canonicalize_url(u) for u in queue}
    idx = 0
    while idx < len(queue):
      if options.max_pages is not None and len(chapters) >= options.max_pages:
        break
      target_url = queue[idx]
      use_soup = initial_soup if _canonicalize_url(target_url) == initial_key else None
      article = consume_page(target_url, soup=use_soup)
      if article is None:
        idx += 1
        continue
      extra = _extract_content_urls(article, base_url=target_url, start_url=url)
      for link in extra:
        key = _canonicalize_url(link)
        if key in discovered:
          continue
        discovered.add(key)
        queue.append(link)
      idx += 1
    return chapters

  # Fallback: follow next/previous navigation.
  current_url = url
  soup = initial_soup
  while True:
    if options.max_pages is not None and len(chapters) >= options.max_pages:
      break

    article = consume_page(current_url, soup=soup)
    if article is None:
      break

    next_url = _extract_next_url(soup, base_url=base_url)
    if not next_url:
      break

    current_url = next_url
    soup = fetch_soup(current_url)

  return chapters
