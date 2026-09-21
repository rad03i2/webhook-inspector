import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from webhook_inspector.core import Store
from webhook_inspector.server import Receiver


def test_receiver_captures_request(tmp_path):
    store = Store(tmp_path / "events.db")
    handler = type("TestReceiver", (Receiver,), {"store": store})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/github?ignored=yes"
        req = urllib.request.Request(url, data=b'{"action":"ping"}', headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3) as response:
            payload = json.loads(response.read())
            assert response.status == 202 and payload["ok"] is True
        event = store.get(payload["event_id"])
        assert event.path == "/github"
        assert event.body == b'{"action":"ping"}'
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
