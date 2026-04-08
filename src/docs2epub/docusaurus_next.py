from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from markdown import markdown as render_markdown

from .model import Chapter


DEFAULT_USER_AGENT = "docs2epub/0.1 (+https://github.com/brenorb/docs2epub)"
_MARKDOWN_EXTENSIONS = (".md", ".markdown", ".mdx")
_GITHUB_MOVED_MARKDOWN_RE = re.compile(r"^\s*\[Moved to [^\]]+\]\(([^)]+)\)\s*$", re.DOTALL)
_GITHUB_BOOK_NUMBER_RE = re.compile(r"^(?:factor|appendix|chapter)-0*(\d+)\b")

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


def _github_repo_parts(url: str) -> tuple[str, str, str, str, str, list[str]] | None:
  parsed = urlparse(url)
  host = parsed.netloc.lower()
  if host not in {"github.com", "www.github.com"}:
    return None
  parts = [part for part in parsed.path.split("/") if part]
  if len(parts) < 4 or parts[2] not in {"blob", "tree"}:
    return None
  owner, repo, kind = parts[:3]
  return parsed.scheme or "https", host, owner, repo, kind, parts[3:]


def _derive_github_tree_ref(start_url: str, current_path: str | None) -> str | None:
  repo_parts = _github_repo_parts(start_url)
  if repo_parts is None:
    return None

  _, _, _, _, kind, tail_parts = repo_parts
  if kind != "tree" or not tail_parts:
    return None

  path_parts = [part for part in (current_path or "").split("/") if part]
  if path_parts and len(tail_parts) > len(path_parts) and tail_parts[-len(path_parts) :] == path_parts:
    ref_parts = tail_parts[: -len(path_parts)]
    if ref_parts:
      return "/".join(ref_parts)

  return tail_parts[0]


def _github_raw_ref_prefix(ref_type: str) -> str | None:
  value = ref_type.strip().lower()
  if value == "branch":
    return "refs/heads"
  if value == "tag":
    return "refs/tags"
  return None


def _build_github_raw_url(
  *,
  scheme: str,
  host: str,
  owner: str,
  repo: str,
  item_path: str,
  ref_name: str | None,
  ref_type: str | None,
  fallback_ref: str | None,
) -> str | None:
  path = item_path.strip("/")
  if not path:
    return None

  if ref_name:
    ref_prefix = _github_raw_ref_prefix(ref_type or "")
    if ref_prefix:
      return f"{scheme}://{host}/{owner}/{repo}/raw/{ref_prefix}/{ref_name}/{path}"

  if fallback_ref:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{fallback_ref}/{path}"

  return None


def _extract_github_tree_markdown_urls(soup: BeautifulSoup, *, start_url: str) -> list[str]:
  repo_parts = _github_repo_parts(start_url)
  if repo_parts is None:
    return []

  scheme, host, owner, repo, kind, _ = repo_parts
  if kind != "tree":
    return []

  seen: set[str] = set()
  urls: list[str] = []

  scripts = soup.select('script[data-target="react-app.embeddedData"]')
  for script in scripts:
    raw = script.string or script.get_text()
    if not raw.strip():
      continue
    try:
      payload = json.loads(raw)
    except json.JSONDecodeError:
      continue

    route = payload.get("payload", {}).get("codeViewTreeRoute", {})
    items = route.get("tree", {}).get("items", [])
    current_path = route.get("path")
    ref_info = route.get("refInfo", {})
    ref_name = str(ref_info.get("name") or "").strip() or None
    ref_type = str(ref_info.get("refType") or "").strip() or None
    ref = _derive_github_tree_ref(start_url, current_path)
    if not ref_name and ref:
      ref_name = ref
    if not ref_name and not ref:
      continue

    for item in items:
      if item.get("contentType") != "file":
        continue
      item_path = str(item.get("path") or "").strip("/")
      if not item_path.lower().endswith(_MARKDOWN_EXTENSIONS):
        continue
      url = _build_github_raw_url(
        scheme=scheme,
        host=host,
        owner=owner,
        repo=repo,
        item_path=item_path,
        ref_name=ref_name,
        ref_type=ref_type,
        fallback_ref=ref,
      )
      if not url:
        continue
      canonical = _canonicalize_url(url)
      if canonical in seen:
        continue
      seen.add(canonical)
      urls.append(url)

    if urls:
      return sorted(urls, key=_github_markdown_sort_key)

  for a in soup.find_all("a", href=True):
    href = str(a.get("href") or "").strip()
    if not href:
      continue
    abs_url = urljoin(start_url, href)
    parsed = urlparse(abs_url)
    if parsed.netloc.lower() != host:
      continue
    if "/blob/" not in parsed.path:
      continue
    if not parsed.path.lower().endswith(_MARKDOWN_EXTENSIONS):
      continue
    canonical = _canonicalize_url(abs_url)
    if canonical in seen:
      continue
    seen.add(canonical)
    repo_parts = _github_repo_parts(abs_url)
    if repo_parts is None:
      continue
    _, _, _, _, _, tail_parts = repo_parts
    item_path = "/".join(tail_parts[1:])
    raw_url = _build_github_raw_url(
      scheme=scheme,
      host=host,
      owner=owner,
      repo=repo,
      item_path=item_path,
      ref_name=tail_parts[0] if tail_parts else None,
      ref_type=None,
      fallback_ref=tail_parts[0] if tail_parts else None,
    )
    if raw_url:
      urls.append(raw_url)

  return sorted(urls, key=_github_markdown_sort_key)


def _extract_github_blob_raw_url(soup: BeautifulSoup, *, start_url: str) -> str | None:
  parsed = urlparse(start_url)
  if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
    return None
  if not parsed.path.lower().endswith(_MARKDOWN_EXTENSIONS):
    return None

  raw_link = soup.select_one('a[data-testid="raw-button"][href]')
  if not raw_link:
    return None

  href = str(raw_link.get("href") or "").strip()
  if not href:
    return None

  raw_url = urljoin(start_url, href)
  parsed_raw = urlparse(raw_url)
  if parsed_raw.scheme not in ("http", "https"):
    return None
  return _canonicalize_url(raw_url)


def _github_markdown_sort_key(url: str) -> tuple[int, int, str]:
  path = (urlparse(url).path or "").strip("/")
  name = path.rsplit("/", 1)[-1].lower()
  match = _GITHUB_BOOK_NUMBER_RE.match(name)
  if match:
    return (1, int(match.group(1)), name)
  return (0, 0, name)


def _extract_markdown_redirect_target(markdown_text: str) -> str | None:
  match = _GITHUB_MOVED_MARKDOWN_RE.match(markdown_text.strip())
  if not match:
    return None
  return match.group(1).strip() or None


def _markdown_to_html(markdown_text: str) -> Tag:
  html = render_markdown(markdown_text, extensions=["extra", "sane_lists"])
  soup = BeautifulSoup(f"<body>{html}</body>", "lxml")
  body = soup.find("body")
  if body is None:
    raise RuntimeError("Could not render markdown body")
  return body


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
      if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
        el["href"] = urljoin(base_url, href)
    if el.has_attr("src"):
      src = str(el.get("src") or "")
      if src and not src.startswith(("data:", "cid:")):
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

  github_tree_urls = _extract_github_tree_markdown_urls(initial_soup, start_url=url)
  github_blob_raw_url = _extract_github_blob_raw_url(initial_soup, start_url=url)
  sidebar_urls = _extract_sidebar_urls(initial_soup, base_url=base_url, start_url=url)
  initial_key = _canonicalize_url(url)
  github_markdown_seen: set[str] = set()

  def consume_github_markdown(raw_url: str) -> None:
    current_url = raw_url
    redirects_seen: set[str] = set()

    while True:
      key = _canonicalize_url(current_url)
      if key in redirects_seen:
        return
      redirects_seen.add(key)

      try:
        resp = session.get(current_url, timeout=30)
        resp.raise_for_status()
      except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in {404, 410}:
          return
        raise

      redirect_target = _extract_markdown_redirect_target(resp.text)
      if redirect_target:
        current_url = urljoin(current_url, redirect_target)
        continue

      final_key = _canonicalize_url(current_url)
      if final_key in github_markdown_seen:
        return
      github_markdown_seen.add(final_key)

      article = _markdown_to_html(resp.text)
      _absolutize_urls(article, base_url=current_url)
      title_el = article.find(re.compile(r"^h[1-6]$"))
      title = (
        " ".join(title_el.get_text(" ", strip=True).split())
        if title_el
        else f"Chapter {len(chapters) + 1}"
      )
      if title_el and " ".join(title_el.get_text(" ", strip=True).split()) == title:
        title_el.decompose()
      html = article.decode_contents()
      chapters.append(Chapter(index=len(chapters) + 1, title=title, url=current_url, html=html))

      if options.sleep_s > 0 and (options.max_pages is None or len(chapters) < options.max_pages):
        import time

        time.sleep(options.sleep_s)

      return

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
    title_el = article.find(re.compile(r"^h[1-6]$"))
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

    for a in list(article.select('a.hash-link[href^="#"], a.anchor[href^="#"]')):
      a.decompose()

    html = article.decode_contents()
    chapters.append(Chapter(index=len(chapters) + 1, title=title, url=target_url, html=html))

    if options.sleep_s > 0 and (options.max_pages is None or len(chapters) < options.max_pages):
      import time

      time.sleep(options.sleep_s)

    return article

  if github_tree_urls:
    for target_url in github_tree_urls:
      if options.max_pages is not None and len(chapters) >= options.max_pages:
        break
      consume_github_markdown(target_url)
    return chapters

  if github_blob_raw_url:
    consume_github_markdown(github_blob_raw_url)
    return chapters

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
