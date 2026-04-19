from __future__ import annotations

import sqlite3
from pathlib import Path

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.recorder import build_sqlite_recorder
from delivery_flow.observability.config import resolve_project_context
from delivery_flow.observability.sqlite_store import SQLiteObservabilityStore


def test_sqlite_store_bootstraps_expected_tables_and_user_version(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"

    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]

    assert tables == {
        "projects",
        "runs",
        "tasks",
        "task_loops",
        "task_dispatches",
        "events",
        "run_scm_context",
        "run_summary",
        "task_summary",
        "loop_summary",
        "task_dispatch_summary",
    }
    assert user_version == 1


def test_project_context_uses_root_name_for_non_git_projects(tmp_path: Path) -> None:
    root = tmp_path / "plain-project"
    root.mkdir()

    context = resolve_project_context(project_root=root, skill_name="delivery-flow")

    assert context.project_name == "plain-project"
    assert context.project_root == root
    assert context.scm_type == "none"
    assert context.branch is None


def test_sqlite_store_scopes_task_identity_to_each_run(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"

    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    with store.transaction() as conn:
        conn.execute(
            """
            INSERT INTO projects (project_id, project_name, project_root, skill_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("project-1", "plain-project", str(tmp_path), "delivery-flow", "2026-04-19T00:00:00Z"),
        )
        conn.executemany(
            """
            INSERT INTO runs (run_id, project_id, mode, started_at, owner_acceptance_required)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("run-1", "project-1", "superpowers-backed", "2026-04-19T00:00:01Z", 1),
                ("run-2", "project-1", "superpowers-backed", "2026-04-19T00:00:02Z", 1),
            ],
        )
        conn.executemany(
            """
            INSERT INTO tasks (run_id, task_id, task_order, title, goal, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("run-1", "task-1", 1, "Task", "First run task", "pending"),
                ("run-2", "task-1", 1, "Task", "Second run task", "pending"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO task_summary (run_id, task_id, latest_event_at, loop_count, dispatch_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("run-1", "task-1", "2026-04-19T00:01:00Z", 1, 1),
                ("run-2", "task-1", "2026-04-19T00:02:00Z", 1, 1),
            ],
        )
        conn.executemany(
            """
            INSERT INTO task_loops (loop_id, task_id, run_id, loop_index, final_review_result)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("loop-1", "task-1", "run-1", 1, "pass"),
                ("loop-2", "task-1", "run-2", 1, "pass"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO task_dispatches (
                dispatch_id, task_id, run_id, loop_id, dispatch_index, selected_stage
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("dispatch-1", "task-1", "run-1", "loop-1", 1, "running_dev"),
                ("dispatch-2", "task-1", "run-2", "loop-2", 1, "running_dev"),
            ],
        )

        task_rows = conn.execute(
            "SELECT run_id, task_id, goal FROM tasks WHERE task_id = ? ORDER BY run_id",
            ("task-1",),
        ).fetchall()
        summary_rows = conn.execute(
            "SELECT run_id, task_id FROM task_summary WHERE task_id = ? ORDER BY run_id",
            ("task-1",),
        ).fetchall()
        loop_rows = conn.execute(
            "SELECT run_id, task_id, loop_id FROM task_loops WHERE task_id = ? ORDER BY run_id",
            ("task-1",),
        ).fetchall()
        dispatch_rows = conn.execute(
            """
            SELECT run_id, task_id, dispatch_id
            FROM task_dispatches
            WHERE task_id = ?
            ORDER BY run_id
            """,
            ("task-1",),
        ).fetchall()

    assert task_rows == [
        ("run-1", "task-1", "First run task"),
        ("run-2", "task-1", "Second run task"),
    ]
    assert summary_rows == [("run-1", "task-1"), ("run-2", "task-1")]
    assert loop_rows == [("run-1", "task-1", "loop-1"), ("run-2", "task-1", "loop-2")]
    assert dispatch_rows == [
        ("run-1", "task-1", "dispatch-1"),
        ("run-2", "task-1", "dispatch-2"),
    ]


def test_sqlite_store_uses_run_scoped_primary_keys_for_tasks_and_task_summary(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "observability.sqlite3"

    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    with sqlite3.connect(db_path) as conn:
        tasks_table_info = conn.execute("PRAGMA table_info(tasks)").fetchall()
        task_summary_table_info = conn.execute("PRAGMA table_info(task_summary)").fetchall()

        assert [(row[1], row[5]) for row in tasks_table_info if row[5]] == [
            ("run_id", 1),
            ("task_id", 2),
        ]
        assert [(row[1], row[5]) for row in task_summary_table_info if row[5]] == [
            ("run_id", 1),
            ("task_id", 2),
        ]


def seed_sample_run(store: SQLiteObservabilityStore, project_root: Path) -> str:
    recorder = build_sqlite_recorder(
        db_path=store.db_path,
        project_root=project_root,
        skill_name="delivery-flow",
    )
    run_id = recorder.record_run_started(mode="superpowers-backed")
    recorder.record_task_registered(
        run_id=run_id,
        task=PlanTaskArtifact(
            task_id="task-2",
            title="Task 1",
            goal="Execute task-2",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder.record_task_registered(
        run_id=run_id,
        task=PlanTaskArtifact(
            task_id="task-10",
            title="Task 2",
            goal="Execute task-10",
            verification_commands=["uv run pytest"],
        ),
        task_order=2,
    )
    recorder.record_task_loop_started(run_id=run_id, task_id="task-2", loop_index=1)
    recorder.record_task_dispatched(
        run_id=run_id,
        task_id="task-2",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder.record_review(run_id=run_id, task_id="task-2", loop_index=1, normalized_result="pass")
    recorder.record_task_loop_started(run_id=run_id, task_id="task-10", loop_index=1)
    recorder.record_task_dispatched(
        run_id=run_id,
        task_id="task-10",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder.record_review(run_id=run_id, task_id="task-10", loop_index=1, normalized_result="blocker")
    recorder.record_task_loop_started(run_id=run_id, task_id="task-10", loop_index=2)
    recorder.record_task_dispatched(
        run_id=run_id,
        task_id="task-10",
        loop_index=2,
        dispatch_index=2,
        selected_stage="running_fix",
    )
    recorder.record_review(run_id=run_id, task_id="task-10", loop_index=2, normalized_result="pass")
    recorder.record_run_completed(
        run_id=run_id,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )
    return run_id


def test_queries_return_run_task_loop_and_dispatch_summaries(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"
    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()
    run_id = seed_sample_run(store, tmp_path)

    from delivery_flow.observability.queries import ObservabilityQueries

    queries = ObservabilityQueries(store)

    run_summary = queries.list_runs()
    task_summary = queries.list_tasks(run_id=run_id)
    loop_summary = queries.list_task_loops(run_id=run_id, task_id="task-10")
    dispatch_summary = queries.list_task_dispatches(run_id=run_id, task_id="task-10")

    assert run_summary[0]["stop_reason"] == "pass"
    assert [row["task_id"] for row in task_summary] == ["task-2", "task-10"]
    assert task_summary[1]["total_loops"] == 2
    assert loop_summary[1]["final_review_result"] == "pass"
    assert dispatch_summary[1]["selected_stage"] == "running_fix"
