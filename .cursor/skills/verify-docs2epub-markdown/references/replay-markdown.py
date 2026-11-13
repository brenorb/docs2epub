from unittest.mock import patch

import requests
from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next

origin = "https://docs.example.test"
start = f"{origin}/docs/intro"
pages = {
    start: '<article><h1>Intro</h1></article><a href="/llms.txt">Index</a>',
    f"{origin}/llms.txt": "\n".join(f"{origin}/docs/{name}.md" for name in ("first", "second", "cycle")),
    f"{origin}/docs/first.md": '[Moved to final](final.md)',
    f"{origin}/docs/second.md": '[Moved to final](final.md)',
    f"{origin}/docs/cycle.md": '[Moved to cycle](cycle.md)',
    f"{origin}/docs/final.md": "# Final\n\nShared chapter",
}
calls = []
def get(url, *, timeout):
    calls.append(url)
    response = requests.Response()
    response.url = url
    response.status_code = 200
    response.encoding = "utf-8"
    response._content = pages[url].encode()
    return response

with patch("requests.Session.get", side_effect=get):
    chapters = iter_docusaurus_next(DocusaurusNextOptions(start, sleep_s=0))
assert [chapter.url for chapter in chapters] == [f"{origin}/docs/final.md"], chapters
assert calls.count(f"{origin}/docs/final.md") == 2
assert calls.count(f"{origin}/docs/cycle.md") == 1
print("Markdown convergence and cycle checked")
