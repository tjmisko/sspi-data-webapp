"""Customize pages inject the username into an inline script. For a logged-out
visitor the fallback must serialize as JSON, not as an autoescaped string:
`&#34;&#34;` is a syntax error that stops every handler on the page."""
import re

import pytest


def _username_assignment(html):
    match = re.search(r"window\.sspiUsername = (.*?);", html)
    assert match, "page no longer assigns window.sspiUsername"
    return match.group(1)


@pytest.mark.parametrize("path, expected", [
    ("/customize/load", '""'),
    ("/customize/builder", "null"),
])
def test_should_serialize_anonymous_username_as_json_when_logged_out(client, path, expected):
    response = client.get(path)
    assert response.status_code == 200
    assignment = _username_assignment(response.get_data(as_text=True))
    assert assignment == expected
    assert "&#" not in assignment
