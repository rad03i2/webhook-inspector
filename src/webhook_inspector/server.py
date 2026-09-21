from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .core import MAX_BODY, Store


class Receiver(BaseHTTPRequestHandler):
    store: Store
    server_version = "WebhookInspector/1.0"

    def _receive(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "invalid Content-Length"); return
        if length < 0 or length > MAX_BODY:
            self.send_error(413, "body exceeds 1 MiB"); return
        body = self.rfile.read(length) if length else b""
        headers = {k: v for k, v in self.headers.items()}
        path = urlsplit(self.path).path
        event_id = self.store.add(self.command, path, self.client_address[0], headers, body)
        payload = json.dumps({"ok": True, "event_id": event_id}).encode()
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    do_GET = _receive
    do_POST = _receive
    do_PUT = _receive
    do_PATCH = _receive
    do_DELETE = _receive
    do_HEAD = _receive

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")


def serve(store: Store, host: str = "127.0.0.1", port: int = 8787) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    handler = type("ConfiguredReceiver", (Receiver,), {"store": store})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Webhook Inspector listening on http://{host}:{port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
