#!/usr/bin/env python3
"""Tests for Claude Code hook."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_send_formulas import has_formulas

import hook_send_formulas


def make_stdin_mock(data: str):
    """Create a stdin mock with .buffer attribute returning BytesIO."""
    mock = MagicMock()
    mock.buffer = io.BytesIO(data.encode('utf-8'))
    return mock


class TestHookInputParsing(unittest.TestCase):
    """Tests for parsing input data from Claude Code."""

    def _run_hook(self, input_data: str) -> str | None:
        """Runs main() with mocked stdin and captures send_response calls."""
        sent = []

        def fake_send(text):
            sent.append(text)

        with patch.object(hook_send_formulas, 'send_response', fake_send), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": False}), \
             patch('sys.stdin', make_stdin_mock(input_data)):
            hook_send_formulas.main()

        return sent[0] if sent else None

    def test_claude_code_stop_format(self):
        """Claude Code Stop hook format."""
        data = json.dumps({
            "session_id": "abc-123",
            "hook_event_name": "Stop",
            "last_assistant_message": "Formula: $$\\int x dx = \\frac{x^2}{2}$$"
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)
        self.assertIn("\\int", result)

    def test_no_formulas_no_send(self):
        """No formulas — doesn't send."""
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "Just plain text."
        })
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_empty_message(self):
        """Empty message."""
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": ""
        })
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_invalid_json(self):
        """Invalid JSON doesn't crash."""
        result = self._run_hook("this is not json {{{")
        self.assertIsNone(result)

    def test_missing_last_assistant_message(self):
        """Missing last_assistant_message field."""
        data = json.dumps({"session_id": "abc"})
        result = self._run_hook(data)
        self.assertIsNone(result)

    def test_multiple_formulas_in_response(self):
        """Multiple formulas in one response."""
        text = "From $$E = mc^2$$ and $$F = ma$$ follows $$a = \\frac{F}{m}$$"
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": text
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)
        self.assertEqual(result, text)

    def test_formula_with_markdown(self):
        """Formulas mixed with markdown."""
        text = "## Header\n\nText and formula $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$\n\n- item"
        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": text
        })
        result = self._run_hook(data)
        self.assertIsNotNone(result)


class TestServerHealthCheck(unittest.TestCase):
    """Tests for server health-check based enablement."""

    def test_server_not_running_does_nothing(self):
        """When server is not running — hook exits without parsing."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\int x dx$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'server_status', return_value=None), \
             patch('sys.stdin', make_stdin_mock(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 0)

    def test_server_running_sends(self):
        """When server is running — sends formulas."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\int x dx$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": False}), \
             patch('sys.stdin', make_stdin_mock(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 1)


class TestPauseCheck(unittest.TestCase):
    """Tests for pause check in hook."""

    def test_paused_does_nothing(self):
        """When paused — doesn't parse."""
        sent = []

        data = json.dumps({
            "hook_event_name": "Stop",
            "last_assistant_message": "$$\\sum x$$"
        })

        with patch.object(hook_send_formulas, 'send_response', lambda t: sent.append(t)), \
             patch.object(hook_send_formulas, 'server_status', return_value={"status": "ok", "paused": True}), \
             patch('sys.stdin', make_stdin_mock(data)):
            hook_send_formulas.main()

        self.assertEqual(len(sent), 0)


if __name__ == "__main__":
    unittest.main()
