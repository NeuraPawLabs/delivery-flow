from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.config import resolve_project_context
from delivery_flow.observability.sqlite_store import SQLiteObservabilityStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ObservabilityRecorder:
    store: SQLiteObservabilityStore
    project_root: Path
    skill_name: str

    def record_run_started(self, *, mode: str) -> str:
        project = resolve_project_context(project_root=self.project_root, skill_name=self.skill_name)
        run_id = uuid4().hex
        now = _utc_now()
        with self.store.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO projects (
                    project_id, project_name, project_root, skill_name, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project.project_id,
                    project.project_name,
                    str(project.project_root),
                    project.skill_name,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, project_id, mode, started_at, owner_acceptance_required
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, project.project_id, mode, now, 1),
            )
            conn.execute(
                """
                INSERT INTO run_scm_context (
                    run_id, scm_type, branch, commit_sha, remote_url, default_branch
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    project.scm_type,
                    project.branch,
                    project.commit_sha,
                    project.remote_url,
                    project.default_branch,
                ),
            )
            self._insert_event(
                conn,
                run_id=run_id,
                event_kind="run_started",
                payload={"mode": mode},
                task_id=None,
            )
            conn.execute(
                """
                INSERT INTO run_summary (
                    run_id, mode, started_at, latest_event_at, owner_acceptance_required, task_count, completed_task_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, mode, now, now, 1, 0, 0),
            )
        return run_id

    def record_task_registered(self, *, run_id: str, task: PlanTaskArtifact, task_order: int) -> None:
        now = _utc_now()
        with self.store.transaction() as conn:
            conn.execute(
                """
                INSERT INTO tasks (run_id, task_id, task_order, title, goal, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, task.task_id, task_order, task.title, task.goal, "pending"),
            )
            self._insert_event(
                conn,
                run_id=run_id,
                event_kind="task_registered",
                payload={"task_order": task_order},
                task_id=task.task_id,
            )
            conn.execute(
                """
                INSERT INTO task_summary (
                    run_id, task_id, task_order, title, goal, current_state, latest_event_at, loop_count, dispatch_count,
                    latest_review_result, latest_dispatch_stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, task_id) DO UPDATE SET
                    task_order=excluded.task_order,
                    title=excluded.title,
                    goal=excluded.goal,
                    current_state=excluded.current_state,
                    latest_event_at=excluded.latest_event_at
                """,
                (run_id, task.task_id, task_order, task.title, task.goal, "registered", now, 0, 0, None, None),
            )
            task_count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE run_id = ?",
                (run_id,),
            ).fetchone()[0]
            conn.execute(
                """
                UPDATE run_summary
                SET task_count = ?, latest_event_at = ?
                WHERE run_id = ?
                """,
                (task_count, now, run_id),
            )

    def record_task_loop_started(self, *, run_id: str, task_id: str, loop_index: int, emit_event: bool = True) -> None:
        now = _utc_now()
        loop_id = uuid4().hex
        with self.store.transaction() as conn:
            conn.execute(
                """
                INSERT INTO task_loops (
                    loop_id, run_id, task_id, loop_index, started_at, final_review_result
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (loop_id, run_id, task_id, loop_index, now, None),
            )
            conn.execute(
                """
                INSERT INTO loop_summary (loop_id, run_id, task_id, loop_index, latest_event_at, final_review_result)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(loop_id) DO UPDATE SET
                    latest_event_at=excluded.latest_event_at,
                    final_review_result=excluded.final_review_result
                """,
                (loop_id, run_id, task_id, loop_index, now, None),
            )
            conn.execute(
                """
                UPDATE task_summary
                SET loop_count = ?, current_state = ?, latest_event_at = ?
                WHERE run_id = ? AND task_id = ?
                """,
                (loop_index, "in_progress", now, run_id, task_id),
            )
            if emit_event:
                self._insert_event(
                    conn,
                    run_id=run_id,
                    event_kind="task_loop_started",
                    payload={"loop_index": loop_index},
                    task_id=task_id,
                    loop_id=loop_id,
                )

    def record_task_dispatched(
        self,
        *,
        run_id: str,
        task_id: str,
        loop_index: int,
        dispatch_index: int,
        selected_stage: str,
    ) -> None:
        now = _utc_now()
        with self.store.transaction() as conn:
            loop_id = conn.execute(
                """
                SELECT loop_id
                FROM task_loops
                WHERE run_id = ? AND task_id = ? AND loop_index = ?
                """,
                (run_id, task_id, loop_index),
            ).fetchone()[0]
            dispatch_id = uuid4().hex
            conn.execute(
                """
                INSERT INTO task_dispatches (
                    dispatch_id, run_id, task_id, loop_id, dispatch_index, selected_stage, started_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (dispatch_id, run_id, task_id, loop_id, dispatch_index, selected_stage, now),
            )
            self._insert_event(
                conn,
                run_id=run_id,
                event_kind="task_dispatched",
                payload={"loop_index": loop_index, "selected_stage": selected_stage},
                task_id=task_id,
                loop_id=loop_id,
                dispatch_id=dispatch_id,
            )
            conn.execute(
                """
                INSERT INTO task_dispatch_summary (
                    dispatch_id, run_id, task_id, dispatch_index, latest_event_at, selected_stage
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(dispatch_id) DO UPDATE SET
                    latest_event_at=excluded.latest_event_at,
                    selected_stage=excluded.selected_stage
                """,
                (dispatch_id, run_id, task_id, dispatch_index, now, selected_stage),
            )
            dispatch_count = conn.execute(
                "SELECT COUNT(*) FROM task_dispatches WHERE run_id = ? AND task_id = ?",
                (run_id, task_id),
            ).fetchone()[0]
            conn.execute(
                """
                UPDATE task_summary
                SET dispatch_count = ?, latest_dispatch_stage = ?, latest_event_at = ?
                WHERE run_id = ? AND task_id = ?
                """,
                (dispatch_count, selected_stage, now, run_id, task_id),
            )

    def record_review(self, *, run_id: str, task_id: str, loop_index: int, normalized_result: str) -> None:
        now = _utc_now()
        with self.store.transaction() as conn:
            loop_row = conn.execute(
                """
                SELECT loop_id
                FROM task_loops
                WHERE run_id = ? AND task_id = ? AND loop_index = ?
                """,
                (run_id, task_id, loop_index),
            ).fetchone()
            dispatch_row = conn.execute(
                """
                SELECT dispatch_id
                FROM task_dispatches
                WHERE run_id = ? AND task_id = ? AND loop_id = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (run_id, task_id, loop_row[0] if loop_row is not None else None),
            ).fetchone()
            conn.execute(
                """
                UPDATE task_loops
                SET final_review_result = ?
                WHERE run_id = ? AND task_id = ? AND loop_index = ?
                """,
                (normalized_result, run_id, task_id, loop_index),
            )
            self._insert_event(
                conn,
                run_id=run_id,
                event_kind="review_recorded",
                payload={"loop_index": loop_index, "normalized_result": normalized_result},
                task_id=task_id,
                loop_id=loop_row[0] if loop_row is not None else None,
                dispatch_id=dispatch_row[0] if dispatch_row is not None else None,
            )
            conn.execute(
                """
                UPDATE loop_summary
                SET final_review_result = ?, latest_event_at = ?
                WHERE loop_id = ?
                """,
                (normalized_result, now, loop_row[0] if loop_row is not None else None),
            )
            conn.execute(
                """
                UPDATE task_summary
                SET current_state = ?, latest_review_result = ?, latest_event_at = ?
                WHERE run_id = ? AND task_id = ?
                """,
                (normalized_result, normalized_result, now, run_id, task_id),
            )

    def record_run_completed(
        self,
        *,
        run_id: str,
        final_state: str,
        stop_reason: str,
        owner_acceptance_required: bool,
    ) -> None:
        now = _utc_now()
        with self.store.transaction() as conn:
            conn.execute(
                """
                UPDATE runs
                SET ended_at = ?, final_state = ?, stop_reason = ?, owner_acceptance_required = ?
                WHERE run_id = ?
                """,
                (now, final_state, stop_reason, int(owner_acceptance_required), run_id),
            )
            self._insert_event(
                conn,
                run_id=run_id,
                event_kind="run_completed",
                payload={"stop_reason": stop_reason, "final_state": final_state},
                task_id=None,
            )
            completed_task_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM task_summary
                WHERE run_id = ? AND latest_review_result = 'pass'
                """,
                (run_id,),
            ).fetchone()[0]
            conn.execute(
                """
                UPDATE run_summary
                SET ended_at = ?, latest_event_at = ?, stop_reason = ?, owner_acceptance_required = ?, completed_task_count = ?
                WHERE run_id = ?
                """,
                (now, now, stop_reason, int(owner_acceptance_required), completed_task_count, run_id),
            )

    def query_debug_snapshot(self) -> dict[str, list[dict[str, object]]]:
        with sqlite3.connect(self.store.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return {
                "runs": [
                    dict(row)
                    for row in conn.execute(
                        "SELECT run_id, mode, final_state, stop_reason, owner_acceptance_required FROM runs ORDER BY rowid"
                    )
                ],
                "tasks": [
                    dict(row)
                    for row in conn.execute(
                        "SELECT run_id, task_id, task_order, title, goal, status FROM tasks ORDER BY rowid"
                    )
                ],
                "task_loops": [
                    dict(row)
                    for row in conn.execute(
                        "SELECT loop_id, task_id, loop_index, final_review_result FROM task_loops ORDER BY rowid"
                    )
                ],
                "task_dispatches": [
                    dict(row)
                    for row in conn.execute(
                        "SELECT dispatch_id, task_id, loop_id, dispatch_index, selected_stage FROM task_dispatches ORDER BY rowid"
                    )
                ],
                "events": [
                    dict(row)
                    for row in conn.execute(
                        """
                        SELECT event_kind, event_index, task_id, loop_id, dispatch_id, payload_json
                        FROM events
                        ORDER BY run_id, event_index
                        """
                    )
                ],
            }

    def _insert_event(
        self,
        conn: sqlite3.Connection,
        *,
        run_id: str,
        event_kind: str,
        payload: dict[str, object],
        task_id: str | None,
        loop_id: str | None = None,
        dispatch_id: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO events (
                event_id, run_id, task_id, loop_id, dispatch_id, event_kind, payload_json, created_at, event_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid4().hex,
                run_id,
                task_id,
                loop_id,
                dispatch_id,
                event_kind,
                json.dumps(payload, sort_keys=True),
                _utc_now(),
                conn.execute(
                    "SELECT COALESCE(MAX(event_index), 0) + 1 FROM events WHERE run_id = ?",
                    (run_id,),
                ).fetchone()[0],
            ),
        )


def build_sqlite_recorder(*, db_path: Path, project_root: Path, skill_name: str) -> ObservabilityRecorder:
    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()
    return ObservabilityRecorder(
        store=store,
        project_root=Path(project_root),
        skill_name=skill_name,
    )
