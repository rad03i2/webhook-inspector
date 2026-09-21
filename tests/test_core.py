import hashlib
import hmac

import pytest

from webhook_inspector.core import MAX_BODY, Store, verify_hmac


def test_hmac_verification():
    body = b'{"hello":"world"}'
    sig = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert verify_hmac(body, "sha256=" + sig, "secret")
    assert verify_hmac(body, sig, "secret")
    assert not verify_hmac(body, "0" * 64, "secret")


def test_store_lifecycle(tmp_path):
    store = Store(tmp_path / "events.db")
    first = store.add("post", "/hook", "127.0.0.1", {"Content-Type": "application/json"}, b"{}")
    second = store.add("GET", "/health", "127.0.0.1", {}, b"")
    assert store.get(first).method == "POST"
    assert [e.id for e in store.list()] == [second, first]
    assert [e.id for e in store.list(path="/hook")] == [first]
    assert store.delete(first)
    assert store.get(first) is None


def test_prune(tmp_path):
    store = Store(tmp_path / "events.db")
    for i in range(5): store.add("POST", f"/{i}", "local", {}, str(i).encode())
    assert store.prune(2) == 3
    assert len(store.list()) == 2


def test_limits(tmp_path):
    store = Store(tmp_path / "events.db")
    with pytest.raises(ValueError): store.add("POST", "/", "local", {}, b"x" * (MAX_BODY + 1))
    with pytest.raises(ValueError): store.list(0)
    with pytest.raises(ValueError): store.prune(-1)
