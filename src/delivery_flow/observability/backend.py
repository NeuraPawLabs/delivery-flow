from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class ObservabilityApp:
    queries: ObservabilityQueries

    def handle_json(self, method: str, path: str) -> list[dict[str, object]] | dict[str, object]:
        if method.upper() != "GET":
            return {"status": 405, "error": "method not allowed"}

        if path == "/runs":
            return self.queries.list_runs()

        prefix = "/runs/"
        suffix = "/tasks"
        if path.startswith(prefix) and path.endswith(suffix):
            run_id = path[len(prefix) : -len(suffix)]
            if run_id and "/" not in run_id:
                return self.queries.list_tasks(run_id=run_id)

        return {"status": 404, "error": "not found"}


def build_observability_app(db_path: Path) -> ObservabilityApp:
    return ObservabilityApp(queries=ObservabilityQueries(_ReadOnlyStore(db_path=Path(db_path))))
