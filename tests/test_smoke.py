from docs2epub.epub import EpubMetadata, build_epub
from docs2epub.kindle_html import clean_html_for_kindle_epub2
from docs2epub.model import Chapter


def test_build_epub3_smoke(tmp_path):
  out = tmp_path / "book.epub"
  chapters = [
    Chapter(index=1, title="Hello", url="https://example.com", html="<h1>Hello</h1><p>World</p>"),
  ]
  meta = EpubMetadata(title="T", author="A", language="en")
  path = build_epub(chapters=chapters, out_file=out, meta=meta)
  assert path.exists()
  assert path.stat().st_size > 0


def test_kindle_cleaner_strips_tabindex_and_ol_start():
  cleaned = clean_html_for_kindle_epub2(
    '<div tabindex="0"><ol start="2"><li><u>Hi</u></li></ol></div>',
    keep_images=False,
  )
  assert "tabindex" not in cleaned
  assert "start=" not in cleaned
  assert "underline" in cleaned


def test_kindle_cleaner_drops_remote_images_by_default():
  cleaned = clean_html_for_kindle_epub2(
    '<p>x</p><img src="https://example.com/a.png" /><p>y</p>',
    keep_images=False,
  )
  assert "img" not in cleaned


def test_kindle_cleaner_drops_relative_images_by_default():
  cleaned = clean_html_for_kindle_epub2(
    '<p>x</p><img src="images/a.png" /><p>y</p>',
    keep_images=False,
  )
  assert "img" not in cleaned


def test_kindle_cleaner_rewrites_images_when_enabled():
  cleaned = clean_html_for_kindle_epub2(
    '<p>x</p><img src="images/a.png" srcset="images/a@2x.png 2x" loading="lazy" /><p>y</p>',
    keep_images=True,
    base_url="https://example.com/docs/intro",
    image_rewriter=lambda src, base_url: "assets/a.png",
  )
  assert 'src="assets/a.png"' in cleaned
  assert "srcset=" not in cleaned
  assert "loading=" not in cleaned


def test_kindle_cleaner_deduplicates_ids_and_drops_broken_fragment_links():
  cleaned = clean_html_for_kindle_epub2(
    (
      '<h1 id="intro">Intro</h1>'
      '<p id="intro">Duplicate id</p>'
      '<a href="#intro">ok</a>'
      '<a href="#missing">broken</a>'
    ),
    keep_images=False,
  )
  assert 'id="intro"' in cleaned
  assert 'id="intro-2"' in cleaned
  assert 'href="#intro"' in cleaned
  assert '>broken</a>' in cleaned
  assert 'href="#missing"' not in cleaned


def test_kindle_cleaner_drops_images_without_src_even_when_enabled():
  cleaned = clean_html_for_kindle_epub2(
    "<p>x</p><img /><p>y</p>",
    keep_images=True,
  )
  assert "img" not in cleaned


def test_kindle_cleaner_preserves_newlines_inside_code_blocks():
  cleaned = clean_html_for_kindle_epub2(
    (
      "<pre><code>"
      "my-skill/\n"
      "├── SKILL.md          # Required: metadata + instructions\n"
      "├── scripts/          # Optional: executable code\n"
      "└── assets/           # Optional: templates, resources\n"
      "</code></pre>"
    ),
    keep_images=False,
  )
  assert "my-skill/\n├── SKILL.md" in cleaned
  assert "instructions\n├── scripts/" in cleaned
  assert "code\n└── assets/" in cleaned


def test_kindle_cleaner_preserves_shiki_line_breaks_inside_code_blocks():
  cleaned = clean_html_for_kindle_epub2(
    (
      '<pre class="shiki"><code language="text">'
      '<span class="line"><span>my-skill/</span></span>\n'
      '<span class="line"><span>├── SKILL.md          # Required: metadata + instructions</span></span>\n'
      '<span class="line"><span>├── scripts/          # Optional: executable code</span></span>\n'
      "</code></pre>"
    ),
    keep_images=False,
  )
  assert "</span></span>\n<span class=\"line\">" in cleaned


def test_kindle_cleaner_promotes_data_as_paragraph_spans():
  cleaned = clean_html_for_kindle_epub2(
    (
      "<h3>Provide defaults, not menus</h3>"
      '<span data-as="p">When multiple tools or approaches could work.</span>'
    ),
    keep_images=False,
  )

  assert "<h3>Provide defaults, not menus</h3>" in cleaned
  assert "<p>When multiple tools or approaches could work.</p>" in cleaned
  assert 'data-as="p"' not in cleaned
