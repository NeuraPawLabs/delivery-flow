from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProjectContext:
    project_id: str
    project_name: str
    project_root: Path
    skill_name: str
    scm_type: str
    branch: str | None = None
    commit_sha: str | None = None
    remote_url: str | None = None
    default_branch: str | None = None
