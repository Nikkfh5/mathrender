#!/usr/bin/env python3
"""Тесты HTTP-сервера MathRender."""

import json
import subprocess
import sys
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path

PORT = 18574  # Отдельный порт для тестов, чтобы не мешать рабочему серверу
BASE = f"http://127.0.0.1:{PORT}"
PROJECT_DIR = Path(__file__).parent.parent


def request(method, path, body=None):
    """Отправляет HTTP-запрос к тестовому серверу."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


class TestServer(unittest.TestCase):
    """Тесты эндпоинтов сервера."""

    server_proc = None

    @classmethod
    def setUpClass(cls):
        """Запускаем тестовый сервер на отдельном порту."""
        import tempfile
        cls._env = {
            **__import__("os").environ,
        }
        # Запускаем сервер с изменённым портом
        cls.server_proc = subprocess.Popen(
            [
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, '{PROJECT_DIR}');"
                f"import server; server.PORT = {PORT}; server.main()"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Ждём готовности
        for _ in range(30):
            try:
                urllib.request.urlopen(f"{BASE}/health", timeout=1)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.1)
        else:
            raise RuntimeError("Тестовый сервер не запустился")

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc:
            cls.server_proc.terminate()
            cls.server_proc.wait(timeout=5)

    def setUp(self):
        """Очищаем историю перед каждым тестом."""
        try:
            request("POST", "/clear")
        except Exception:
            pass

    # --- Health ---

    def test_health(self):
        resp = request("GET", "/health")
        self.assertEqual(resp["status"], "ok")

    def test_health_has_paused(self):
        resp = request("GET", "/health")
        self.assertIn("paused", resp)

    # --- Response ---

    def test_post_response(self):
        resp = request("POST", "/response", {
            "text": "Формула: $$\\int x dx$$",
            "timestamp": "12:00:00",
        })
        self.assertTrue(resp["ok"])

    def test_response_appears_in_history(self):
        request("POST", "/response", {
            "text": "Тест: $$e^{i\\pi} + 1 = 0$$",
            "timestamp": "12:00:00",
        })
        history = request("GET", "/history")
        self.assertEqual(len(history), 1)
        self.assertIn("e^{i\\pi}", history[0]["text"])

    def test_multiple_responses(self):
        for i in range(3):
            request("POST", "/response", {
                "text": f"Ответ {i}: $$x = {i}$$",
            })
        history = request("GET", "/history")
        self.assertEqual(len(history), 3)

    # --- Formula (обратная совместимость) ---

    def test_post_formula(self):
        resp = request("POST", "/formula", {
            "formulas": ["\\int_0^1 x dx"],
            "context": "тест",
        })
        self.assertTrue(resp["ok"])
        self.assertEqual(resp["count"], 1)

    # --- Clear ---

    def test_clear(self):
        request("POST", "/response", {"text": "тест $$x$$"})
        history_before = request("GET", "/history")
        self.assertEqual(len(history_before), 1)

        request("POST", "/clear")
        history_after = request("GET", "/history")
        self.assertEqual(len(history_after), 0)

    # --- Pause / Resume ---

    def test_pause_resume(self):
        resp = request("POST", "/pause")
        self.assertTrue(resp["paused"])

        health = request("GET", "/health")
        self.assertTrue(health["paused"])

        resp = request("POST", "/resume")
        self.assertFalse(resp["paused"])

        health = request("GET", "/health")
        self.assertFalse(health["paused"])

    # --- History ---

    def test_empty_history(self):
        history = request("GET", "/history")
        self.assertEqual(history, [])

    def test_history_preserves_order(self):
        for i in range(5):
            request("POST", "/response", {
                "text": f"Ответ {i}",
                "timestamp": f"12:00:0{i}",
            })
        history = request("GET", "/history")
        self.assertEqual(len(history), 5)
        self.assertIn("Ответ 0", history[0]["text"])
        self.assertIn("Ответ 4", history[4]["text"])

    def test_history_has_timestamps(self):
        request("POST", "/response", {
            "text": "Тест",
            "timestamp": "15:30:00",
        })
        history = request("GET", "/history")
        self.assertEqual(history[0]["timestamp"], "15:30:00")


if __name__ == "__main__":
    unittest.main()
