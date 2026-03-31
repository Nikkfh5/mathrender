#!/usr/bin/env python3
"""Тесты хука Claude Code."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_send_formulas import has_formulas

# Импортируем после добавления в path
import hook_send_formulas


class TestHookInputParsing(unittest.TestCase):
    """Тесты парсинга входных данных от Claude Code."""

    def _run_hook(self, input_data: str) -> str | None:
        """Запускает main() хука с подменённым stdin и перехватывает отправку."""
        sent = []

        def fake_send(text):
            sent.append(text)

        with patch.object(hook_send_formulas, 'send_response', fake_send), \
             patch.object(hook_send_formulas, 'is_enabled', return_value=True), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": False}), \
             patch('sys.stdin', __import__('io').StringIO(input_data)):
            hook_send_formulas.main()

        return sent[0] if sent else None

    def test_claude_code_stop_format(self):
        """Формат хука Stop от Claude Code."""
        data = json.dumps({
            "session_id": "abc-123",
            "hook_event_name": "Stop",
            "last_assistant_message": "Формула: $$\\int x dx = \\frac{x^2}{2}$$"
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)
        self.assertIn("\\int", result)

    def test_no_formulas_no_send(self):
        """Если формул нет — не отправляет."""
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "Просто текст без формул."
        })
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_empty_message(self):
        """Пустое сообщение."""
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": ""
        })
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_invalid_json(self):
        """Невалидный JSON не падает."""
        result = self._run_hook("это не json {{{")
        self.assertIsNone(result)

    def test_missing_last_assistant_message(self):
        """Нет поля last_assistant_message."""
        data = json.dumps({"session_id": "abc"})
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_multiple_formulas_in_response(self):
        """Несколько формул в одном ответе."""
        text = "Из $$E = mc^2$$ и $$F = ma$$ следует $$a = \\frac{F}{m}$$"
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": text
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)
        self.assertEqual(result, text)

    def test_formula_with_markdown(self):
        """Формулы вперемешку с markdown."""
        text = "## Заголовок\n\nТекст и формула $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$\n\n- пункт"
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": text
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)


class TestEnabledFlag(unittest.TestCase):
    """Тесты флага .enabled."""

    def test_disabled_does_nothing(self):
        """Когда выключен — хук не парсит и не отправляет."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\int x dx$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'is_enabled', return_value=False), \
             patch('sys.stdin', __import__('io').StringIO(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 0)

    def test_enabled_sends(self):
        """Когда включён — отправляет."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\int x dx$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'is_enabled', return_value=True), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": False}), \
             patch('sys.stdin', __import__('io').StringIO(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 1)


class TestPauseCheck(unittest.TestCase):
    """Тесты проверки паузы в хуке."""

    def test_paused_does_nothing(self):
        """На паузе — не парсит."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\sum x$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'is_enabled', return_value=True), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": True}), \
             patch('sys.stdin', __import__('io').StringIO(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 0)


if __name__ == "__main__":
    unittest.main()
