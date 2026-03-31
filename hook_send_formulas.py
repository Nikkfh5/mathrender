#!/usr/bin/env python3
"""Hook for Claude Code: sends responses with LaTeX formulas to MathRender VS Code extension."""

import json
import re
import sys
import time
import urllib.request
import urllib.error

MATHRENDER_URL = "http://127.0.0.1:18573/response"
MATHRENDER_HEALTH = "http://127.0.0.1:18573/health"

# Quick check: does the text contain something that looks like LaTeX
LATEX_QUICK_CHECK = re.compile(r'\$\$.+?\$\$|\$[^$]+\$|\\\[.+?\\\]|\\\(.+?\\\)', re.DOTALL)


def has_formulas(text: str) -> bool:
    """Quickly checks if text contains LaTeX formulas."""
    return bool(LATEX_QUICK_CHECK.search(text))


def server_status() -> dict | None:
    """Returns server status or None if not running."""
    try:
        with urllib.request.urlopen(MATHRENDER_HEALTH, timeout=1) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError):
        return None


def send_response(text: str):
    """Sends response text to MathRender server."""
    payload = json.dumps({
        "text": text,
        "timestamp": time.strftime("%H:%M:%S"),
    }).encode("utf-8")

    req = urllib.request.Request(
        MATHRENDER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=2):
            pass
    except (urllib.error.URLError, OSError):
        pass


def main():
    # If server is not running, extension is not active — exit silently
    status = server_status()
    if status is None:
        return
    if status.get("paused"):
        return

    input_data = sys.stdin.read()
    try:
        hook_data = json.loads(input_data)
    except json.JSONDecodeError:
        return

    text = hook_data.get("last_assistant_message", "")
    if text and has_formulas(text):
        send_response(text)


if __name__ == "__main__":
    main()
