#!/usr/bin/env python3
"""Хук Claude Code: отправляет ответ с LaTeX-формулами на MathRender-сервер."""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

MATHRENDER_URL = "http://127.0.0.1:18573/response"
MATHRENDER_HEALTH = "http://127.0.0.1:18573/health"
MATHRENDER_DIR = os.path.dirname(os.path.abspath(__file__))

# Быстрая проверка: есть ли в тексте что-то похожее на LaTeX
LATEX_QUICK_CHECK = re.compile(r'\$\$.+?\$\$|\$[^$]+\$|\\\[.+?\\\]|\\\(.+?\\\)', re.DOTALL)


def has_formulas(text: str) -> bool:
    """Быстро проверяет, есть ли в тексте LaTeX-формулы."""
    return bool(LATEX_QUICK_CHECK.search(text))


def server_status() -> dict | None:
    """Возвращает статус сервера или None если не запущен."""
    try:
        with urllib.request.urlopen(MATHRENDER_HEALTH, timeout=1) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError):
        return None


def start_server():
    server_script = os.path.join(MATHRENDER_DIR, "server.py")
    subprocess.Popen(
        ["python3", server_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(20):
        time.sleep(0.1)
        if server_status() is not None:
            break
    subprocess.Popen(
        ["open", "http://127.0.0.1:18573"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def send_response(text: str):
    status = server_status()
    if status is None:
        start_server()
    elif status.get("paused"):
        return

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


def is_enabled() -> bool:
    """Проверяет, включён ли MathRender (файл-флаг .enabled)."""
    return os.path.exists(os.path.join(MATHRENDER_DIR, ".enabled"))


def main():
    if not is_enabled():
        return

    # Проверяем паузу до парсинга
    status = server_status()
    if status and status.get("paused"):
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
