from __future__ import annotations

from pathlib import Path

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.backend import build_observability_app
from delivery_flow.observability.recorder import build_sqlite_recorder


def seed_sample_observability_db(db_path: Path, project_root: Path) -> str:
    recorder = build_sqlite_recorder(
        db_path=db_path,
        project_root=project_root,
        skill_name="delivery-flow",
    )
    run_id = recorder.record_run_started(mode="superpowers-backed")
    recorder.record_task_registered(
        run_id=run_id,
        task=PlanTaskArtifact(
            task_id="task-1",
            title="Task 1",
            goal="Expose task view",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder.record_task_loop_started(run_id=run_id, task_id="task-1", loop_index=1)
    recorder.record_task_dispatched(
        run_id=run_id,
        task_id="task-1",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder.record_review(run_id=run_id, task_id="task-1", loop_index=1, normalized_result="pass")
    recorder.record_run_completed(
        run_id=run_id,
        final_state="completed",
        stop_reason="pass",
        owner_acceptance_required=False,
    )
    return run_id


def test_backend_serves_run_and_task_views_from_existing_database(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"
    run_id = seed_sample_observability_db(db_path, tmp_path)
    app = build_observability_app(db_path)

    runs = app.handle_json("GET", "/runs")
    tasks = app.handle_json("GET", f"/runs/{run_id}/tasks")

    assert runs[0]["run_id"] == run_id
    assert runs[0]["stop_reason"] == "pass"
    assert tasks == [
        {
            "run_id": run_id,
            "task_id": "task-1",
            "task_order": 1,
            "title": "Task 1",
            "goal": "Expose task view",
            "current_state": "pass",
            "loop_count": 1,
            "dispatch_count": 1,
            "latest_review_result": "pass",
            "latest_dispatch_stage": "running_dev",
            "total_loops": 1,
        }
    ]


def test_backend_is_read_only_and_rejects_non_get_requests(tmp_path: Path) -> None:
    app = build_observability_app(tmp_path / "observability.sqlite3")

    response = app.handle_json("POST", "/runs")

    assert response == {"status": 405, "error": "method not allowed"}
