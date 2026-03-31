#!/usr/bin/env python3
"""MathRender v2 — локальный сервер для рендера LaTeX-формул из Claude Code."""

import json
import os
import queue
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 18573  # произвольный свободный порт
MAX_BODY = 1024 * 1024  # 1 МБ максимум

# Очередь SSE-клиентов
clients: list[queue.Queue] = []
clients_lock = threading.Lock()

# История формул за сессию
history: list[dict] = []
history_lock = threading.Lock()

# Пауза — хук проверяет этот флаг
paused = False


def broadcast(event_data: dict):
    """Отправить событие всем подключённым SSE-клиентам."""
    message = f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
    with clients_lock:
        dead = []
        for q in clients:
            try:
                q.put_nowait(message)
            except queue.Full:
                dead.append(q)
        for q in dead:
            clients.remove(q)


class MathHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # тихий сервер

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/events":
            self._handle_sse()
        elif path == "/history":
            self._handle_history()
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "paused": paused}).encode())
        elif path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"paused": paused}).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/formula":
            self._handle_formula()
        elif path == "/response":
            self._handle_response()
        elif path == "/clear":
            self._handle_clear()
        elif path == "/pause":
            self._set_paused(True)
        elif path == "/resume":
            self._set_paused(False)
        else:
            self.send_error(404)

    def _serve_file(self, filename, content_type):
        filepath = Path(__file__).parent / filename
        try:
            content = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {filename}")

    def _read_body(self) -> str:
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            self.send_error(413, "Request too large")
            return ""
        return self.rfile.read(length).decode("utf-8")

    def _handle_formula(self):
        body = self._read_body()
        if not body:
            return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # Если прислали просто текст, оборачиваем
            data = {"formulas": [body]}

        formulas = data.get("formulas", [])
        context = data.get("context", "")
        timestamp = time.strftime("%H:%M:%S")

        entry = {
            "formulas": formulas,
            "context": context,
            "timestamp": timestamp,
        }

        with history_lock:
            history.append(entry)

        broadcast({"type": "formulas", **entry})

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "count": len(formulas)}).encode())

    def _handle_response(self):
        body = self._read_body()
        if not body:
            return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"text": body}

        text = data.get("text", "")
        timestamp = data.get("timestamp", time.strftime("%H:%M:%S"))

        entry = {
            "type": "response",
            "text": text,
            "timestamp": timestamp,
        }

        with history_lock:
            history.append(entry)

        broadcast(entry)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def _set_paused(self, value):
        global paused
        paused = value
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"paused": paused}).encode())

    def _handle_clear(self):
        with history_lock:
            history.clear()
        broadcast({"type": "clear"})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def _handle_history(self):
        with history_lock:
            data = list(history)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors_headers()
        self.end_headers()

        q = queue.Queue(maxsize=100)
        with clients_lock:
            clients.append(q)

        try:
            # Отправляем начальный пинг
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()

            while True:
                try:
                    message = q.get(timeout=15)
                    self.wfile.write(message.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # keepalive
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with clients_lock:
                if q in clients:
                    clients.remove(q)


class ThreadedHTTPServer(HTTPServer):
    """Обрабатываем каждый запрос в отдельном потоке."""
    daemon_threads = True

    def process_request(self, request, client_address):
        t = threading.Thread(target=self._handle, args=(request, client_address))
        t.daemon = True
        t.start()

    def _handle(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    pidfile = Path(__file__).parent / ".server.pid"
    pidfile.write_text(str(os.getpid()))

    server = ThreadedHTTPServer((HOST, PORT), MathHandler)
    print(f"MathRender v2 запущен: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен.")
        server.shutdown()
    finally:
        pidfile.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
