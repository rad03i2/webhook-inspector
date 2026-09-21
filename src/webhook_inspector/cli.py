from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .core import Store, verify_hmac
from .server import serve

DEFAULT_DB = Path(os.environ.get("WEBHOOK_INSPECTOR_DB", Path.home() / ".webhook-inspector" / "events.db"))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="webhook-inspector", description="Receive, inspect, verify and replay webhooks locally.")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    p.add_argument("--version", action="version", version="Webhook Inspector 1.0.0 — Radwan Abdulhadi Ahmed / @rad03i2")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("serve", help="start local webhook receiver"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8787)
    s = sub.add_parser("list", help="list captured events"); s.add_argument("--limit", type=int, default=20); s.add_argument("--path")
    s = sub.add_parser("show", help="show one event"); s.add_argument("id", type=int); s.add_argument("--json", action="store_true")
    s = sub.add_parser("verify", help="verify HMAC signature on a captured event"); s.add_argument("id", type=int); s.add_argument("--header", default="X-Hub-Signature-256"); s.add_argument("--secret-env", default="WEBHOOK_SECRET"); s.add_argument("--algorithm", choices=["sha256", "sha1"], default="sha256")
    s = sub.add_parser("replay", help="replay a captured event to a URL"); s.add_argument("id", type=int); s.add_argument("url"); s.add_argument("--timeout", type=float, default=10.0)
    s = sub.add_parser("export", help="export events as JSONL"); s.add_argument("output", type=Path); s.add_argument("--limit", type=int, default=100); s.add_argument("--force", action="store_true")
    s = sub.add_parser("delete", help="delete one event"); s.add_argument("id", type=int); s.add_argument("--yes", action="store_true")
    s = sub.add_parser("prune", help="retain only newest events"); s.add_argument("--keep", type=int, required=True); s.add_argument("--yes", action="store_true")
    return p


def _get(store: Store, event_id: int):
    event = store.get(event_id)
    if not event:
        raise ValueError(f"event {event_id} not found")
    return event


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = Store(args.db)
    try:
        if args.command == "serve":
            serve(store, args.host, args.port); return 0
        if args.command == "list":
            for e in store.list(args.limit, args.path): print(f"{e.id:>6}  {e.received_at}  {e.method:<7} {e.path:<30} {len(e.body)} B")
            return 0
        if args.command == "show":
            e = _get(store, args.id)
            if args.json: print(json.dumps(e.as_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"ID: {e.id}\nTime: {e.received_at}\nMethod: {e.method}\nPath: {e.path}\nRemote: {e.remote_addr}\nHeaders:")
                for k, v in e.headers.items(): print(f"  {k}: {v}")
                print("Body:\n" + e.body.decode("utf-8", errors="replace"))
            return 0
        if args.command == "verify":
            e = _get(store, args.id); signature = next((v for k,v in e.headers.items() if k.lower() == args.header.lower()), None)
            if not signature: raise ValueError(f"header {args.header!r} not present")
            secret = os.environ.get(args.secret_env)
            if not secret: raise ValueError(f"secret environment variable {args.secret_env!r} is not set")
            ok = verify_hmac(e.body, signature, secret, args.algorithm); print("VALID" if ok else "INVALID"); return 0 if ok else 2
        if args.command == "replay":
            e = _get(store, args.id)
            if not args.url.startswith(("http://", "https://")): raise ValueError("replay URL must use http:// or https://")
            blocked = {"host", "content-length", "connection", "transfer-encoding"}
            headers = {k:v for k,v in e.headers.items() if k.lower() not in blocked}
            req = urllib.request.Request(args.url, data=e.body, headers=headers, method=e.method if e.method != "HEAD" else "POST")
            try:
                with urllib.request.urlopen(req, timeout=args.timeout) as r: print(f"{r.status} {r.reason}")
            except urllib.error.HTTPError as exc: print(f"{exc.code} {exc.reason}"); return 2
            return 0
        if args.command == "export":
            if args.output.exists() and not args.force: raise ValueError("output exists; use --force to replace")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            tmp = args.output.with_suffix(args.output.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for e in reversed(store.list(args.limit)): f.write(json.dumps(e.as_dict(), ensure_ascii=False) + "\n")
            tmp.replace(args.output); print(args.output); return 0
        if args.command == "delete":
            if not args.yes: raise ValueError("refusing deletion without --yes")
            if not store.delete(args.id): raise ValueError(f"event {args.id} not found")
            return 0
        if args.command == "prune":
            if not args.yes: raise ValueError("refusing prune without --yes")
            print(f"Deleted {store.prune(args.keep)} event(s)"); return 0
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
