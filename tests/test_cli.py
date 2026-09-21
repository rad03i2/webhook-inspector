from webhook_inspector.cli import main
from webhook_inspector.core import Store


def test_cli_show_and_delete(tmp_path, capsys):
    db = tmp_path / "events.db"
    event_id = Store(db).add("POST", "/hook", "local", {}, b"hello")
    assert main(["--db", str(db), "show", str(event_id), "--json"]) == 0
    assert '"body": "hello"' in capsys.readouterr().out
    assert main(["--db", str(db), "delete", str(event_id)]) == 2
    assert main(["--db", str(db), "delete", str(event_id), "--yes"]) == 0


def test_export_refuses_overwrite(tmp_path):
    db, out = tmp_path / "events.db", tmp_path / "events.jsonl"
    Store(db).add("POST", "/", "local", {}, b"{}")
    assert main(["--db", str(db), "export", str(out)]) == 0
    assert out.exists()
    assert main(["--db", str(db), "export", str(out)]) == 2
    assert main(["--db", str(db), "export", str(out), "--force"]) == 0
