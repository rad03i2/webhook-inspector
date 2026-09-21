from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

MAX_BODY = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_hmac(body: bytes, signature: str, secret: str, algorithm: str = "sha256") -> bool:
    """Verify common webhook signatures such as sha256=<hex> or bare hex."""
    if algorithm not in {"sha256", "sha1"}:
        raise ValueError("algorithm must be sha256 or sha1")
    if not secret:
        raise ValueError("secret must not be empty")
    supplied = signature.strip()
    prefix = algorithm + "="
    if supplied.lower().startswith(prefix):
        supplied = supplied[len(prefix):]
    digestmod = hashlib.sha256 if algorithm == "sha256" else hashlib.sha1
    expected = hmac.new(secret.encode("utf-8"), body, digestmod).hexdigest()
    return hmac.compare_digest(expected.lower(), supplied.lower())


@dataclass(frozen=True)
class Event:
    id: int
    received_at: str
    method: str
    path: str
    remote_addr: str
    headers: dict[str, str]
    body: bytes

    def as_dict(self, include_body: bool = True) -> dict:
        data = {
            "id": self.id, "received_at": self.received_at, "method": self.method,
            "path": self.path, "remote_addr": self.remote_addr, "headers": self.headers,
            "size": len(self.body),
        }
        if include_body:
            data["body"] = self.body.decode("utf-8", errors="replace")
        return data


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init(self) -> None:
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL, method TEXT NOT NULL, path TEXT NOT NULL,
                remote_addr TEXT NOT NULL, headers_json TEXT NOT NULL, body BLOB NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_events_received ON events(received_at DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_events_path ON events(path)")

    def add(self, method: str, path: str, remote_addr: str, headers: dict[str, str], body: bytes) -> int:
        if len(body) > MAX_BODY:
            raise ValueError("request body exceeds 1 MiB")
        with self.connect() as db:
            cur = db.execute(
                "INSERT INTO events(received_at,method,path,remote_addr,headers_json,body) VALUES(?,?,?,?,?,?)",
                (utc_now(), method.upper(), path, remote_addr, json.dumps(headers, ensure_ascii=False), body),
            )
            return int(cur.lastrowid)

    @staticmethod
    def _event(row: sqlite3.Row) -> Event:
        return Event(row["id"], row["received_at"], row["method"], row["path"], row["remote_addr"], json.loads(row["headers_json"]), bytes(row["body"]))

    def get(self, event_id: int) -> Event | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        return self._event(row) if row else None

    def list(self, limit: int = 20, path: str | None = None) -> list[Event]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        sql, args = "SELECT * FROM events", []
        if path:
            sql += " WHERE path=?"; args.append(path)
        sql += " ORDER BY id DESC LIMIT ?"; args.append(limit)
        with self.connect() as db:
            return [self._event(r) for r in db.execute(sql, args).fetchall()]

    def delete(self, event_id: int) -> bool:
        with self.connect() as db:
            cur = db.execute("DELETE FROM events WHERE id=?", (event_id,))
            return cur.rowcount > 0

    def prune(self, keep: int) -> int:
        if keep < 0:
            raise ValueError("keep must be >= 0")
        with self.connect() as db:
            if keep == 0:
                cur = db.execute("DELETE FROM events")
            else:
                cur = db.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT ?)", (keep,))
            return cur.rowcount
