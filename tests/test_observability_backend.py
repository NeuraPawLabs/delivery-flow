from __future__ import annotations

from pathlib import Path

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.backend import build_observability_app
from delivery_flow.observability.config import resolve_project_context
from delivery_flow.observability.recorder import build_sqlite_recorder


def seed_multi_project_observability_db(db_path: Path, root: Path) -> dict[str, str]:
    project_a_root = root / "project-a"
    project_b_root = root / "project-b"
    project_a_root.mkdir()
    project_b_root.mkdir()

    recorder_a = build_sqlite_recorder(
        db_path=db_path,
        project_root=project_a_root,
        skill_name="delivery-flow",
    )
    run_a = recorder_a.record_run_started(mode="fallback")
    recorder_a.record_task_registered(
        run_id=run_a,
        task=PlanTaskArtifact(
            task_id="task-1",
            title="Task A1",
            goal="Expose task view",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder_a.record_task_loop_started(run_id=run_a, task_id="task-1", loop_index=1)
    recorder_a.record_task_dispatched(
        run_id=run_a,
        task_id="task-1",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder_a.record_review(run_id=run_a, task_id="task-1", loop_index=1, normalized_result="pass")
    recorder_a.record_run_completed(
        run_id=run_a,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )

    recorder_b = build_sqlite_recorder(
        db_path=db_path,
        project_root=project_b_root,
        skill_name="delivery-flow",
    )
    run_b1 = recorder_b.record_run_started(mode="superpowers-backed")
    recorder_b.record_task_registered(
        run_id=run_b1,
        task=PlanTaskArtifact(
            task_id="task-1",
            title="Task B1",
            goal="Inspect project runs",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder_b.record_task_loop_started(run_id=run_b1, task_id="task-1", loop_index=1)
    recorder_b.record_task_dispatched(
        run_id=run_b1,
        task_id="task-1",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder_b.record_review(run_id=run_b1, task_id="task-1", loop_index=1, normalized_result="blocker")
    recorder_b.record_task_loop_started(run_id=run_b1, task_id="task-1", loop_index=2)
    recorder_b.record_task_dispatched(
        run_id=run_b1,
        task_id="task-1",
        loop_index=2,
        dispatch_index=2,
        selected_stage="running_fix",
    )
    recorder_b.record_review(run_id=run_b1, task_id="task-1", loop_index=2, normalized_result="pass")
    recorder_b.record_run_completed(
        run_id=run_b1,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )

    run_b2 = recorder_b.record_run_started(mode="superpowers-backed")
    recorder_b.record_task_registered(
        run_id=run_b2,
        task=PlanTaskArtifact(
            task_id="task-1",
            title="Task B2",
            goal="Latest run first",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder_b.record_task_loop_started(run_id=run_b2, task_id="task-1", loop_index=1)
    recorder_b.record_task_dispatched(
        run_id=run_b2,
        task_id="task-1",
        loop_index=1,
        dispatch_index=1,
        selected_stage="running_dev",
    )
    recorder_b.record_review(run_id=run_b2, task_id="task-1", loop_index=1, normalized_result="pass")
    recorder_b.record_run_completed(
        run_id=run_b2,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )

    return {
        "project_a_id": resolve_project_context(project_a_root, "delivery-flow").project_id,
        "project_b_id": resolve_project_context(project_b_root, "delivery-flow").project_id,
        "run_a": run_a,
        "run_b1": run_b1,
        "run_b2": run_b2,
    }


def test_backend_serves_multi_project_views_with_pagination_and_stable_order(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.sqlite3"
    ids = seed_multi_project_observability_db(db_path, tmp_path)
    app = build_observability_app(db_path)

    projects = app.handle_json("GET", "/api/projects?limit=10&offset=0")
    project_runs = app.handle_json("GET", f"/api/projects/{ids['project_b_id']}/runs?limit=10&offset=0")
    run_detail = app.handle_json("GET", f"/api/runs/{ids['run_b2']}")
    run_tasks = app.handle_json("GET", f"/api/runs/{ids['run_b1']}/tasks?limit=10&offset=0")
    run_events = app.handle_json("GET", f"/api/runs/{ids['run_b1']}/events?limit=20&offset=0")
    task_loops = app.handle_json("GET", f"/api/runs/{ids['run_b1']}/tasks/task-1/loops?limit=10&offset=0")
    task_dispatches = app.handle_json("GET", f"/api/runs/{ids['run_b1']}/tasks/task-1/dispatches?limit=10&offset=0")

    assert [item["project_name"] for item in projects["items"]] == ["project-b", "project-a"]
    assert projects["limit"] == 10
    assert projects["offset"] == 0

    assert [item["run_id"] for item in project_runs["items"]] == [ids["run_b2"], ids["run_b1"]]
    assert run_detail["run_id"] == ids["run_b2"]
    assert run_detail["project_id"] == ids["project_b_id"]
    assert run_detail["mode"] == "superpowers-backed"

    assert run_tasks == {
        "items": [
            {
                "run_id": ids["run_b1"],
                "task_id": "task-1",
                "task_order": 1,
                "title": "Task B1",
                "goal": "Inspect project runs",
                "current_state": "pass",
                "loop_count": 2,
                "dispatch_count": 2,
                "latest_review_result": "pass",
                "latest_dispatch_stage": "running_fix",
                "total_loops": 2,
            }
        ],
        "limit": 10,
        "offset": 0,
    }

    assert [item["event_index"] for item in run_events["items"]] == list(range(1, 10))
    assert [item["loop_index"] for item in task_loops["items"]] == [1, 2]
    assert [item["selected_stage"] for item in task_dispatches["items"]] == ["running_dev", "running_fix"]


def test_backend_reports_health_and_rejects_non_get_requests(tmp_path: Path) -> None:
    app = build_observability_app(tmp_path / "observability.sqlite3")

    health = app.handle_json("GET", "/api/health")
    response = app.handle_json("POST", "/api/projects")

    assert health == {"status": "ok"}
    assert response == {"status": 405, "error": "method not allowed"}
