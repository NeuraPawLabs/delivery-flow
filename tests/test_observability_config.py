from __future__ import annotations

from pathlib import Path, PureWindowsPath

from delivery_flow.observability.config import (
    DEFAULT_DATA_DIRNAME,
    DEFAULT_DB_FILENAME,
    default_delivery_flow_home,
    resolve_observability_db_path,
)


def test_default_delivery_flow_home_prefers_delivery_flow_home_env(monkeypatch) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", "/tmp/delivery-flow-home")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    home = default_delivery_flow_home()

    assert home == Path("/tmp/delivery-flow-home")


def test_default_delivery_flow_home_uses_xdg_data_home_on_posix(monkeypatch) -> None:
    monkeypatch.delenv("DELIVERY_FLOW_HOME", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/xdg-data")
    monkeypatch.setattr("delivery_flow.observability.config.os.name", "posix")
    monkeypatch.setattr("delivery_flow.observability.config.Path.home", lambda: Path("/ignored-home"))

    home = default_delivery_flow_home()

    assert home == Path("/tmp/xdg-data") / "delivery-flow"


def test_default_delivery_flow_home_uses_appdata_on_windows(monkeypatch) -> None:
    monkeypatch.delenv("DELIVERY_FLOW_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("APPDATA", r"C:\Users\alice\AppData\Roaming")
    monkeypatch.setattr("delivery_flow.observability.config.os.name", "nt")
    monkeypatch.setattr("delivery_flow.observability.config.Path", PureWindowsPath)

    home = default_delivery_flow_home()

    assert home == PureWindowsPath(r"C:\Users\alice\AppData\Roaming") / "delivery-flow"


def test_resolve_observability_db_path_uses_global_home_by_default(monkeypatch) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", "/tmp/delivery-flow-home")

    assert resolve_observability_db_path() == Path("/tmp/delivery-flow-home") / DEFAULT_DB_FILENAME


def test_resolve_observability_db_path_keeps_project_local_path_when_project_root_is_explicit(
    tmp_path: Path,
) -> None:
    assert resolve_observability_db_path(tmp_path) == tmp_path / DEFAULT_DATA_DIRNAME / DEFAULT_DB_FILENAME
