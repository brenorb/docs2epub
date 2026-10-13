from bs4 import BeautifulSoup


def promote_paragraph_blocks(container: BeautifulSoup) -> None:
  """Preserve block semantics used by documentation frontends."""
  for el in list(container.select('[data-as="p"]')):
    paragraph = container.new_tag("p")
    for attr, value in el.attrs.items():
      if attr != "data-as":
        paragraph[attr] = value
    for child in list(el.contents):
      paragraph.append(child)
    el.replace_with(paragraph)
