from __future__ import annotations

import json
from pathlib import Path

from delivery_flow.contracts import PlanTaskArtifact
from delivery_flow.observability.recorder import build_sqlite_recorder
from delivery_flow.observability.service import ObservabilityService, ServiceResponse, build_observability_service


def _seed_service_db(db_path: Path, project_root: Path) -> None:
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
            goal="Serve api response",
            verification_commands=["uv run pytest"],
        ),
        task_order=1,
    )
    recorder.record_run_completed(
        run_id=run_id,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )


def test_service_serves_api_and_static_index_html(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.db"
    static_root = tmp_path / "static"
    static_root.mkdir()
    (static_root / "index.html").write_text("<html><body>observability ui</body></html>", encoding="utf-8")
    _seed_service_db(db_path, tmp_path / "project-a")

    service = build_observability_service(db_path=db_path, static_root=static_root)

    index_response = service.handle("GET", "/")
    api_response = service.handle("GET", "/api/health")
    projects_response = service.handle("GET", "/api/projects?limit=10&offset=0")

    assert index_response.status == 200
    assert index_response.content_type == "text/html; charset=utf-8"
    assert index_response.body == b"<html><body>observability ui</body></html>"
    assert api_response == ServiceResponse(
        status=200,
        content_type="application/json",
        body=b'{"status": "ok"}',
        json={"status": "ok"},
    )
    assert json.loads(projects_response.body)["items"][0]["project_name"] == "project-a"


def test_service_returns_not_found_when_static_file_is_missing(tmp_path: Path) -> None:
    service = ObservabilityService(
        app=build_observability_service(db_path=tmp_path / "observability.db", static_root=tmp_path).app,
        static_root=tmp_path,
    )

    response = service.handle("GET", "/")

    assert response.status == 404
    assert response.content_type == "text/plain; charset=utf-8"
