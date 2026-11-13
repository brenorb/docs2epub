import os
from unittest.mock import patch

import requests
from docs2epub.docusaurus_next import DocusaurusNextOptions, iter_docusaurus_next

start = "https://docs.example.test/docs/intro"
following = "https://docs.example.test/docs/second"
seen = []

def get(url, *, timeout):
    seen.append(url)
    response = requests.Response()
    response.url = url
    response.status_code = 200 if url == start else 503
    response._content = (
        b'<article><h1>Intro</h1><p>Chapter one</p></article>'
        b'<nav aria-label="Docs pages"><a href="/docs/second">Next</a></nav>'
    )
    return response

with patch("requests.Session.get", side_effect=get):
    if os.environ.get("DOCS2EPUB_EXPECT_STOP"):
        chapters = iter_docusaurus_next(DocusaurusNextOptions(start, max_pages=1, sleep_s=0))
        assert len(chapters) == 1
        assert seen == [start], seen
    else:
        try:
            iter_docusaurus_next(DocusaurusNextOptions(start, max_pages=1, sleep_s=0))
        except requests.HTTPError as error:
            assert error.response.status_code == 503
        else:
            raise AssertionError("Expected the unnecessary fetch to propagate its error")
        assert seen == [start, following], seen
print("Next request path reproduced")
