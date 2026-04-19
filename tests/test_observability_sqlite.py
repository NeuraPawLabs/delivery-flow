from __future__ import annotations

import sqlite3
from pathlib import Path

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.recorder import build_sqlite_recorder
from delivery_flow.observability.config import (
    DEFAULT_DATA_DIRNAME,
    DEFAULT_DB_FILENAME,
    DEFAULT_OBSERVABILITY_DIRNAME,
    resolve_observability_db_path,
    resolve_project_context,
)
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
    assert user_version == 2


def test_project_context_uses_root_name_for_non_git_projects(tmp_path: Path) -> None:
    root = tmp_path / "plain-project"
    root.mkdir()

    context = resolve_project_context(project_root=root, skill_name="delivery-flow")

    assert context.project_name == "plain-project"
    assert context.project_root == root
    assert context.scm_type == "none"
    assert context.branch is None


def test_default_observability_db_path_stays_global_even_when_project_root_is_provided(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "delivery-flow-home"))

    assert resolve_observability_db_path(tmp_path) == (
        tmp_path / "delivery-flow-home" / DEFAULT_OBSERVABILITY_DIRNAME / DEFAULT_DB_FILENAME
    )


def test_default_observability_db_path_uses_global_observability_subdirectory_when_project_root_is_omitted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "delivery-flow-home"))

    assert resolve_observability_db_path() == (
        tmp_path / "delivery-flow-home" / DEFAULT_OBSERVABILITY_DIRNAME / DEFAULT_DB_FILENAME
    )


def test_sqlite_store_bootstraps_events_with_explicit_run_scoped_event_index(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"

    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    with sqlite3.connect(db_path) as conn:
        events_table_info = conn.execute("PRAGMA table_info(events)").fetchall()
        event_indexes = [row for row in events_table_info if row[1] == "event_index"]
        event_index_unique_indexes = conn.execute("PRAGMA index_list(events)").fetchall()

    assert event_indexes == [(8, "event_index", "INTEGER", 1, None, 0)]
    assert any(row[1] == "idx_events_run_id_event_index" and row[2] for row in event_index_unique_indexes)


def test_sqlite_store_migrates_existing_events_to_explicit_event_index(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"

    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE projects (
                project_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                project_root TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(project_root, skill_name)
            );
            CREATE TABLE runs (
                run_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                final_state TEXT,
                stop_reason TEXT,
                owner_acceptance_required INTEGER NOT NULL
            );
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                task_id TEXT,
                loop_id TEXT,
                dispatch_id TEXT,
                event_kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            PRAGMA user_version = 1;
            """
        )
        conn.execute(
            """
            INSERT INTO projects (project_id, project_name, project_root, skill_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("project-1", "plain-project", str(tmp_path), "delivery-flow", "2026-04-19T00:00:00Z"),
        )
        conn.execute(
            """
            INSERT INTO runs (run_id, project_id, mode, started_at, owner_acceptance_required)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("run-1", "project-1", "superpowers-backed", "2026-04-19T00:00:01Z", 1),
        )
        conn.executemany(
            """
            INSERT INTO events (
                event_id, run_id, task_id, loop_id, dispatch_id, event_kind, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("event-1", "run-1", None, None, None, "run_started", "{}", "2026-04-19T00:00:01Z"),
                ("event-2", "run-1", "task-1", None, None, "task_registered", "{}", "2026-04-19T00:00:02Z"),
            ],
        )

    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT event_id, event_index FROM events WHERE run_id = ? ORDER BY event_index",
            ("run-1",),
        ).fetchall()
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]

    assert rows == [("event-1", 1), ("event-2", 2)]
    assert user_version == 2


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


def test_recorder_persists_explicit_event_index_per_run(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"
    store = SQLiteObservabilityStore.connect(db_path)
    store.initialize()

    run_id = seed_sample_run(store, tmp_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT event_kind, event_index
            FROM events
            WHERE run_id = ?
            ORDER BY event_index
            """,
            (run_id,),
        ).fetchall()

    assert rows == [
        ("run_started", 1),
        ("task_registered", 2),
        ("task_registered", 3),
        ("task_loop_started", 4),
        ("task_dispatched", 5),
        ("review_recorded", 6),
        ("task_loop_started", 7),
        ("task_dispatched", 8),
        ("review_recorded", 9),
        ("task_loop_started", 10),
        ("task_dispatched", 11),
        ("review_recorded", 12),
        ("run_completed", 13),
    ]
