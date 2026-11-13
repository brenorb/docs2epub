import os
from unittest.mock import patch

import requests
from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next

origin = "https://docs.example.test"
start = f"{origin}/docs/intro"
nested = f"{origin}/docs/nested/first"
correct = f"{origin}/docs/nested/second"
incorrect = f"{origin}/docs/second"
calls = []
links = {start: "/docs/nested/first", nested: "second"}

def get(url, *, timeout):
    calls.append(url)
    response = requests.Response()
    response.url = url
    response.status_code = 200
    content = "<article><h1>Chapter</h1><p>Text</p></article>"
    if url in links:
        content += f'<nav aria-label="Docs pages"><a href="{links[url]}">Next</a></nav>'
    response._content = content.encode()
    return response

with patch("requests.Session.get", side_effect=get):
    chapters = iter_docusaurus_next(DocusaurusNextOptions(start, sleep_s=0))
expected = correct if os.environ.get("DOCS2EPUB_CURRENT_NEXT_BASE") else incorrect
assert calls == [start, nested, expected], calls
assert chapters[-1].url == expected
print("Relative Next resolution checked")
