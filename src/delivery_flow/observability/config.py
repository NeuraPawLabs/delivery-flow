from __future__ import annotations

import hashlib
from pathlib import Path

from delivery_flow.observability.models import ProjectContext


DEFAULT_DB_FILENAME = "observability.sqlite3"


def resolve_observability_db_path(project_root: Path, db_name: str = DEFAULT_DB_FILENAME) -> Path:
    return project_root / ".delivery-flow" / db_name


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
