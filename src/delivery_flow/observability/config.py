from __future__ import annotations

import hashlib
import os
from pathlib import Path

from delivery_flow.observability.models import ProjectContext


DEFAULT_DATA_DIRNAME = ".delivery_flow"
DEFAULT_DB_FILENAME = "observability.db"
DEFAULT_HOME_DIRNAME = "delivery-flow"
DEFAULT_OBSERVABILITY_DIRNAME = "observability"


def default_delivery_flow_home() -> Path:
    configured_home = os.environ.get("DELIVERY_FLOW_HOME")
    if configured_home:
        return Path(configured_home)

    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / DEFAULT_HOME_DIRNAME
        return Path.home() / "AppData" / "Roaming" / DEFAULT_HOME_DIRNAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / DEFAULT_HOME_DIRNAME
    return Path.home() / ".local" / "share" / DEFAULT_HOME_DIRNAME


def resolve_observability_db_path(
    project_root: Path | None = None,
    db_name: str = DEFAULT_DB_FILENAME,
) -> Path:
    _ = project_root
    return default_delivery_flow_home() / DEFAULT_OBSERVABILITY_DIRNAME / db_name


def resolve_project_context(project_root: Path, skill_name: str) -> ProjectContext:
    root = project_root.resolve()
    scm_type = "git" if (root / ".git").exists() else "none"
    project_name = root.name or root.anchor
    project_key = f"{root}:{skill_name}"
    project_id = hashlib.sha256(project_key.encode("utf-8")).hexdigest()[:16]

    return ProjectContext(
        project_id=project_id,
        project_name=project_name,
        project_root=root,
        skill_name=skill_name,
        scm_type=scm_type,
        branch=None,
        commit_sha=None,
        remote_url=None,
        default_branch=None,
    )
