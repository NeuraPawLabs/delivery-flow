from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from delivery_flow.observability.models import SCHEMA_VERSION


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        project_root TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(project_root, skill_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        mode TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        final_state TEXT,
        stop_reason TEXT,
        owner_acceptance_required INTEGER NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        task_order INTEGER NOT NULL,
        title TEXT NOT NULL,
        goal TEXT NOT NULL,
        status TEXT,
        PRIMARY KEY (run_id, task_id),
        FOREIGN KEY(run_id) REFERENCES runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_loops (
        loop_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        loop_index INTEGER NOT NULL,
        started_at TEXT,
        ended_at TEXT,
        final_review_result TEXT,
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_dispatches (
        dispatch_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        loop_id TEXT,
        dispatch_index INTEGER NOT NULL,
        selected_stage TEXT NOT NULL,
        started_at TEXT,
        ended_at TEXT,
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id),
        FOREIGN KEY(loop_id) REFERENCES task_loops(loop_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT,
        loop_id TEXT,
        dispatch_id TEXT,
        event_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES runs(run_id),
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id),
        FOREIGN KEY(loop_id) REFERENCES task_loops(loop_id),
        FOREIGN KEY(dispatch_id) REFERENCES task_dispatches(dispatch_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS run_scm_context (
        run_id TEXT PRIMARY KEY,
        scm_type TEXT NOT NULL,
        branch TEXT,
        commit_sha TEXT,
        remote_url TEXT,
        default_branch TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS run_summary (
        run_id TEXT PRIMARY KEY,
        mode TEXT,
        started_at TEXT,
        ended_at TEXT,
        latest_event_at TEXT,
        stop_reason TEXT,
        owner_acceptance_required INTEGER,
        task_count INTEGER NOT NULL DEFAULT 0,
        completed_task_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(run_id) REFERENCES runs(run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_summary (
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        task_order INTEGER,
        title TEXT,
        goal TEXT,
        current_state TEXT,
        latest_event_at TEXT,
        loop_count INTEGER NOT NULL DEFAULT 0,
        dispatch_count INTEGER NOT NULL DEFAULT 0,
        latest_review_result TEXT,
        latest_dispatch_stage TEXT,
        PRIMARY KEY (run_id, task_id),
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS loop_summary (
        loop_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        loop_index INTEGER,
        latest_event_at TEXT,
        final_review_result TEXT,
        FOREIGN KEY(loop_id) REFERENCES task_loops(loop_id),
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_dispatch_summary (
        dispatch_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        dispatch_index INTEGER,
        latest_event_at TEXT,
        selected_stage TEXT NOT NULL,
        FOREIGN KEY(dispatch_id) REFERENCES task_dispatches(dispatch_id),
        FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
    )
    """,
)


class SQLiteObservabilityStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @classmethod
    def connect(cls, db_path: Path) -> "SQLiteObservabilityStore":
        return cls(db_path=Path(db_path))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.transaction() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def fetch_all(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            return list(connection.execute(sql, params))
