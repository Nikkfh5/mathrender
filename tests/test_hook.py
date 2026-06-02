#!/usr/bin/env python3
"""Tests for supported agent hooks."""

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import hook_send_formulas


def make_stdin_mock(data: str):
    """Create a stdin mock with .buffer attribute returning BytesIO."""
    mock = MagicMock()
    mock.buffer = io.BytesIO(data.encode('utf-8'))
    return mock


class TestHookInputParsing(unittest.TestCase):
    """Tests for parsing input data from supported agent hooks."""

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

    def test_codex_stop_format(self):
        """Codex Stop hook format."""
        data = json.dumps({
            "session_id": "abc-123",
            "turn_id": "turn-456",
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": "Codex formula: $$E = mc^2$$",
        })
        result = self._run_hook(data)
        self.assertEqual(result, "Codex formula: $$E = mc^2$$")

    def test_extract_response_text_from_last_assistant_message(self):
        """Shared helper reads Claude/Codex assistant messages."""
        text = hook_send_formulas.extract_response_text({
            "hook_event_name": "Stop",
            "last_assistant_message": "Formula: $$x^2$$",
        })
        self.assertEqual(text, "Formula: $$x^2$$")

    def test_extract_response_text_from_text_fallback(self):
        """Shared helper accepts direct text payloads."""
        text = hook_send_formulas.extract_response_text({
            "source": "manual",
            "text": "Formula: $$\\alpha$$",
        })
        self.assertEqual(text, "Formula: $$\\alpha$$")

    def test_extract_response_text_ignores_non_string_fields(self):
        """Non-string payload fields are ignored."""
        text = hook_send_formulas.extract_response_text({
            "last_assistant_message": None,
            "text": ["$$x$$"],
        })
        self.assertEqual(text, "")

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


class TestSendResponse(unittest.TestCase):
    """Tests for send_response resilience."""

    def test_send_response_ignores_http_500(self):
        """Server returning 500 is silently ignored."""
        err = urllib.error.HTTPError(
            url='http://127.0.0.1:18573/response',
            code=500, msg='Internal Server Error', hdrs=None, fp=None,
        )
        with patch('urllib.request.urlopen', side_effect=err):
            hook_send_formulas.send_response("$$x^2$$")  # must not raise

    def test_send_response_ignores_http_400(self):
        """Server returning 400 is silently ignored."""
        err = urllib.error.HTTPError(
            url='http://127.0.0.1:18573/response',
            code=400, msg='Bad Request', hdrs=None, fp=None,
        )
        with patch('urllib.request.urlopen', side_effect=err):
            hook_send_formulas.send_response("$$x^2$$")

    def test_send_response_ignores_connection_refused(self):
        """Connection refused is silently ignored."""
        err = urllib.error.URLError('Connection refused')
        with patch('urllib.request.urlopen', side_effect=err):
            hook_send_formulas.send_response("$$x^2$$")


class TestServerStatus(unittest.TestCase):
    """Tests for server_status resilience."""

    def test_server_status_returns_none_on_invalid_json(self):
        """Malformed JSON from /health returns None instead of crashing."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'not-valid-json{'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch('urllib.request.urlopen', return_value=mock_resp):
            result = hook_send_formulas.server_status()
        self.assertIsNone(result)

    def test_server_status_returns_none_on_url_error(self):
        """URLError (server down) returns None."""
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('down')):
            result = hook_send_formulas.server_status()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
