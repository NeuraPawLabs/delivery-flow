from __future__ import annotations

from pathlib import Path

from delivery_flow.observability.cli import main, parse_args
from delivery_flow.observability.config import resolve_observability_db_path


def test_parse_args_defaults_use_global_db_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "delivery-flow-home"))

    args = parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.db_path == resolve_observability_db_path()
    assert args.static_root is None


def test_parse_args_accepts_explicit_db_path_and_static_root(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.db"
    static_root = tmp_path / "web-dist"

    args = parse_args(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--db-path",
            str(db_path),
            "--static-root",
            str(static_root),
        ]
    )

    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.db_path == db_path
    assert args.static_root == static_root


def test_main_delegates_to_serve(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def fake_serve(*, host: str, port: int, db_path: Path, static_root: Path | None) -> None:
        observed.update(host=host, port=port, db_path=db_path, static_root=static_root)

    monkeypatch.setattr("delivery_flow.observability.cli.serve", fake_serve)

    exit_code = main(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "8123",
            "--db-path",
            str(tmp_path / "observability.db"),
            "--static-root",
            str(tmp_path / "dist"),
        ]
    )

    assert exit_code == 0
    assert observed == {
        "host": "0.0.0.0",
        "port": 8123,
        "db_path": tmp_path / "observability.db",
        "static_root": tmp_path / "dist",
    }
