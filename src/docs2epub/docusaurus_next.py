from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from .model import Chapter


DEFAULT_USER_AGENT = "docs2epub/0.1 (+https://github.com/brenorb/docs2epub)"


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
  raise RuntimeError("Could not find <article> in page HTML")


def _remove_unwanted(article: Tag) -> None:
  for selector in [
    'nav[aria-label="Breadcrumbs"]',
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

  idx = 1
  while True:
    if options.max_pages is not None and idx > options.max_pages:
      break

    if url in visited:
      break
    visited.add(url)

    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    article = _extract_article(soup)

    title_el = article.find(["h1", "h2"])
    title = (
      " ".join(title_el.get_text(" ", strip=True).split()) if title_el else f"Chapter {idx}"
    )

    _remove_unwanted(article)
    _absolutize_urls(article, base_url=base_url)

    for a in list(article.select('a.hash-link[href^="#"]')):
      a.decompose()

    html = article.decode_contents()

    chapters.append(Chapter(index=idx, title=title, url=url, html=html))

    next_url = _extract_next_url(soup, base_url=base_url)
    if not next_url:
      break

    url = next_url
    idx += 1

    if options.sleep_s > 0:
      import time

      time.sleep(options.sleep_s)

  return chapters
