#!/usr/bin/env python3
"""Tests for user-facing WebView text."""

import re
from pathlib import Path


WEBVIEW_HTML = Path(__file__).parent.parent / "extension" / "media" / "index.html"


def test_webview_language_is_english():
    html = WEBVIEW_HTML.read_text(encoding="utf-8")
    assert '<html lang="en">' in html


def test_webview_has_no_cyrillic_user_facing_text():
    html = WEBVIEW_HTML.read_text(encoding="utf-8")
    assert re.search(r"[А-Яа-яЁё]", html) is None
