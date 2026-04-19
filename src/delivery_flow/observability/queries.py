from __future__ import annotations

import json

from delivery_flow.observability.sqlite_store import SQLiteObservabilityStore


class ObservabilityQueries:
    def __init__(self, store: SQLiteObservabilityStore) -> None:
        self.store = store

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT run_id, mode, started_at, ended_at, stop_reason, owner_acceptance_required
                FROM run_summary
                ORDER BY started_at DESC, rowid DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        ]

    def list_projects(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT
                    p.project_id,
                    p.project_name,
                    p.project_root,
                    COUNT(r.run_id) AS run_count,
                    MAX(r.started_at) AS latest_run_at,
                    (
                        SELECT rs.stop_reason
                        FROM runs r2
                        LEFT JOIN run_summary rs ON rs.run_id = r2.run_id
                        WHERE r2.project_id = p.project_id
                        ORDER BY r2.started_at DESC, r2.rowid DESC
                        LIMIT 1
                    ) AS latest_stop_reason
                FROM projects p
                LEFT JOIN runs r ON r.project_id = p.project_id
                GROUP BY p.project_id, p.project_name, p.project_root
                ORDER BY latest_run_at DESC, p.project_name ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        ]

    def get_project(self, *, project_id: str) -> dict[str, object] | None:
        rows = self.store.fetch_all(
            """
            SELECT project_id, project_name, project_root, skill_name, created_at
            FROM projects
            WHERE project_id = ?
            """,
            (project_id,),
        )
        return dict(rows[0]) if rows else None

    def list_project_runs(self, *, project_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT
                    r.run_id,
                    r.project_id,
                    r.mode,
                    r.started_at,
                    r.ended_at,
                    COALESCE(rs.stop_reason, r.stop_reason) AS stop_reason,
                    COALESCE(rs.owner_acceptance_required, r.owner_acceptance_required) AS owner_acceptance_required
                FROM runs r
                LEFT JOIN run_summary rs ON rs.run_id = r.run_id
                WHERE r.project_id = ?
                ORDER BY r.started_at DESC, r.rowid DESC
                LIMIT ? OFFSET ?
                """,
                (project_id, limit, offset),
            )
        ]

    def get_run(self, *, run_id: str) -> dict[str, object] | None:
        rows = self.store.fetch_all(
            """
            SELECT
                r.run_id,
                r.project_id,
                r.mode,
                r.started_at,
                r.ended_at,
                r.final_state,
                COALESCE(rs.stop_reason, r.stop_reason) AS stop_reason,
                COALESCE(rs.owner_acceptance_required, r.owner_acceptance_required) AS owner_acceptance_required,
                rs.task_count,
                rs.completed_task_count
            FROM runs r
            LEFT JOIN run_summary rs ON rs.run_id = r.run_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        )
        return dict(rows[0]) if rows else None

    def list_tasks(self, *, run_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [
            {
                **dict(row),
                "total_loops": row["loop_count"],
            }
            for row in self.store.fetch_all(
                """
                SELECT run_id, task_id, task_order, title, goal, current_state, loop_count, dispatch_count,
                       latest_review_result, latest_dispatch_stage
                FROM task_summary
                WHERE run_id = ?
                ORDER BY task_order ASC, task_id ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, limit, offset),
            )
        ]

    def list_run_events(self, *, run_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [
            {
                **dict(row),
                "payload": json.loads(row["payload_json"]),
            }
            for row in self.store.fetch_all(
                """
                SELECT event_id, run_id, event_index, task_id, loop_id, dispatch_id, event_kind, payload_json, created_at
                FROM events
                WHERE run_id = ?
                ORDER BY event_index ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, limit, offset),
            )
        ]

    def list_task_loops(
        self,
        *,
        run_id: str,
        task_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT loop_id, run_id, task_id, loop_index, final_review_result
                FROM loop_summary
                WHERE run_id = ? AND task_id = ?
                ORDER BY loop_index ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, task_id, limit, offset),
            )
        ]

    def list_task_dispatches(
        self,
        *,
        run_id: str,
        task_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT dispatch_id, run_id, task_id, dispatch_index, selected_stage
                FROM task_dispatch_summary
                WHERE run_id = ? AND task_id = ?
                ORDER BY dispatch_index ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, task_id, limit, offset),
            )
        ]
