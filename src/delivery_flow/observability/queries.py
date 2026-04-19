from __future__ import annotations

from delivery_flow.observability.sqlite_store import SQLiteObservabilityStore


class ObservabilityQueries:
    def __init__(self, store: SQLiteObservabilityStore) -> None:
        self.store = store

    def list_runs(self) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT run_id, mode, started_at, ended_at, stop_reason, owner_acceptance_required
                FROM run_summary
                ORDER BY started_at DESC, rowid DESC
                """
            )
        ]

    def list_tasks(self, *, run_id: str) -> list[dict[str, object]]:
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
                ORDER BY task_order, task_id
                """,
                (run_id,),
            )
        ]

    def list_task_loops(self, *, run_id: str, task_id: str) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT loop_id, run_id, task_id, loop_index, final_review_result
                FROM loop_summary
                WHERE run_id = ? AND task_id = ?
                ORDER BY loop_index
                """,
                (run_id, task_id),
            )
        ]

    def list_task_dispatches(self, *, run_id: str, task_id: str) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT dispatch_id, run_id, task_id, dispatch_index, selected_stage
                FROM task_dispatch_summary
                WHERE run_id = ? AND task_id = ?
                ORDER BY dispatch_index
                """,
                (run_id, task_id),
            )
        ]
