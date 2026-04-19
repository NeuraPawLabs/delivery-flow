from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from delivery_flow.observability.queries import ObservabilityQueries


@dataclass(frozen=True)
class _ReadOnlyStore:
    db_path: Path

    def fetch_all(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        if not self.db_path.exists():
            return []

        connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            return list(connection.execute(sql, params))
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return []
            raise
        finally:
            connection.close()


def _parse_pagination(path: str) -> tuple[str, int, int]:
    parsed = urlparse(path)
    params = parse_qs(parsed.query)
    limit = max(1, int(params.get("limit", ["50"])[0]))
    offset = max(0, int(params.get("offset", ["0"])[0]))
    return parsed.path, limit, offset


@dataclass(frozen=True)
class ObservabilityApp:
    queries: ObservabilityQueries

    def handle_json(self, method: str, path: str) -> dict[str, object]:
        if method.upper() != "GET":
            return {"status": 405, "error": "method not allowed"}

        route, limit, offset = _parse_pagination(path)
        if route == "/api/health":
            return {"status": "ok"}

        if route == "/api/projects":
            return {
                "items": self.queries.list_projects(limit=limit, offset=offset),
                "limit": limit,
                "offset": offset,
            }

        project_prefix = "/api/projects/"
        project_runs_suffix = "/runs"
        if route.startswith(project_prefix) and route.endswith(project_runs_suffix):
            project_id = route[len(project_prefix) : -len(project_runs_suffix)]
            if project_id and "/" not in project_id:
                return {
                    "items": self.queries.list_project_runs(project_id=project_id, limit=limit, offset=offset),
                    "limit": limit,
                    "offset": offset,
                }

        if route.startswith(project_prefix):
            project_id = route[len(project_prefix) :]
            if project_id and "/" not in project_id:
                project = self.queries.get_project(project_id=project_id)
                return project or {"status": 404, "error": "not found"}

        run_prefix = "/api/runs/"
        if route.startswith(run_prefix):
            remainder = route[len(run_prefix) :]
            parts = [part for part in remainder.split("/") if part]
            if len(parts) == 1:
                run = self.queries.get_run(run_id=parts[0])
                return run or {"status": 404, "error": "not found"}

            if len(parts) == 2 and parts[1] == "tasks":
                return {
                    "items": self.queries.list_tasks(run_id=parts[0], limit=limit, offset=offset),
                    "limit": limit,
                    "offset": offset,
                }

            if len(parts) == 2 and parts[1] == "events":
                return {
                    "items": self.queries.list_run_events(run_id=parts[0], limit=limit, offset=offset),
                    "limit": limit,
                    "offset": offset,
                }

            if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "loops":
                return {
                    "items": self.queries.list_task_loops(
                        run_id=parts[0],
                        task_id=parts[2],
                        limit=limit,
                        offset=offset,
                    ),
                    "limit": limit,
                    "offset": offset,
                }

            if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "dispatches":
                return {
                    "items": self.queries.list_task_dispatches(
                        run_id=parts[0],
                        task_id=parts[2],
                        limit=limit,
                        offset=offset,
                    ),
                    "limit": limit,
                    "offset": offset,
                }

        return {"status": 404, "error": "not found"}


def build_observability_app(db_path: Path) -> ObservabilityApp:
    return ObservabilityApp(queries=ObservabilityQueries(_ReadOnlyStore(db_path=Path(db_path))))
