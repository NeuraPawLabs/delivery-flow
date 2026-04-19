from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from delivery_flow.controller import resume_delivery_flow, run_delivery_flow
from delivery_flow.contracts import (
    DeliveryArtifact,
    PlanArtifact,
    PlanTaskArtifact,
    ResumeContextArtifact,
    ResumeRequestArtifact,
    ReviewArtifact,
    RuntimeResult,
    TaskExecutionContext,
)
from delivery_flow.runtime.models import ControllerState, StopReason


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _frontmatter_value(document: str, key: str) -> str:
    lines = document.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("Expected frontmatter block")

    for line in lines[1:]:
        if line == "---":
            break
        prefix = f"{key}:"
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip().strip('"')

    raise AssertionError(f"Missing frontmatter key: {key}")


def _summary_without_mode_line(summary: str) -> str:
    return "\n".join(summary.splitlines()[1:])


def _mode_line(summary: str) -> str:
    return summary.splitlines()[0]


def _normalized(document: str) -> str:
    return re.sub(r"\s+", " ", document).strip().lower()


def _assert_matches(document: str, pattern: str) -> None:
    assert re.search(pattern, _normalized(document)), pattern


class ScriptedProvider:
    def __init__(
        self,
        review_results: list[dict[str, object]],
        *,
        finalize_result: dict[str, object] | None = None,
    ) -> None:
        self.review_results = list(review_results)
        self.finalize_result = finalize_result

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return {
            "summary": "delivery-flow contract",
            "tasks": [
                {
                    "task_id": "task-1",
                    "title": "Task 1",
                    "goal": "Execute task-1",
                    "verification_commands": ["uv run pytest"],
                },
                {
                    "task_id": "task-2",
                    "title": "Task 2",
                    "goal": "Execute task-2",
                    "verification_commands": ["uv run pytest"],
                },
            ],
        }

    def run_dev(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        return {
            "delivery_summary": f"implemented {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id}"],
            "residual_risk": [],
        }

    def run_review(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        if not self.review_results:
            raise AssertionError("run_review called without a scripted review result")
        return self.review_results.pop(0)

    def run_fix(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        return {
            "delivery_summary": f"fixed {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id} --fix"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        return self.finalize_result or {"owner_acceptance_required": False}


def _run_mode(
    *,
    has_superpowers: bool,
    review_results: list[dict[str, object]],
    finalize_result: dict[str, object] | None = None,
):
    return run_delivery_flow(
        payload={"ticket": 301, "goal": "delivery-flow contract"},
        provider=ScriptedProvider(review_results=review_results, finalize_result=finalize_result),
        capability_detector=SimpleNamespace(has_superpowers=has_superpowers),
    )


def _resume_request(*, mode: str, restart_current_task_from_dev: bool = False) -> ResumeRequestArtifact:
    plan = PlanArtifact(
        summary="delivery-flow contract",
        tasks=[
            PlanTaskArtifact(
                task_id="task-1",
                title="Task 1",
                goal="Execute task-1",
                verification_commands=["uv run pytest"],
            ),
            PlanTaskArtifact(
                task_id="task-2",
                title="Task 2",
                goal="Execute task-2",
                verification_commands=["uv run pytest"],
            ),
        ],
    )

    return ResumeRequestArtifact(
        previous_result=RuntimeResult(
            mode=mode,
            final_state=ControllerState.WAITING_FOR_OWNER,
            stop_reason=StopReason.NEEDS_OWNER_DECISION,
            stage_sequence=[
                "discussing_requirement",
                "writing_spec",
                "planning",
                "running_dev",
                "running_review",
                "running_dev",
                "running_review",
                "waiting_for_owner",
            ],
            completed_task_ids=["task-1"],
            pending_task_id="task-2",
            open_issue_summaries=["choose rollout order"],
            owner_acceptance_required=True,
            resume_context=ResumeContextArtifact(
                plan=plan,
                task_index=1,
                latest_delivery=DeliveryArtifact(delivery_summary="implemented task-2"),
                latest_review=ReviewArtifact(
                    raw_result="owner_input_required",
                    findings=["choose rollout order"],
                    owner_decision_reason="choose rollout order",
                ),
            ),
        ),
        owner_response="roll out to canary first",
        restart_current_task_from_dev=restart_current_task_from_dev,
    )


def _resume_mode(
    *,
    has_superpowers: bool,
    review_results: list[dict[str, object]],
    restart_current_task_from_dev: bool = False,
    finalize_result: dict[str, object] | None = None,
):
    mode = "superpowers-backed" if has_superpowers else "fallback"
    return resume_delivery_flow(
        request=_resume_request(mode=mode, restart_current_task_from_dev=restart_current_task_from_dev),
        provider=ScriptedProvider(review_results=review_results, finalize_result=finalize_result),
        capability_detector=SimpleNamespace(has_superpowers=has_superpowers),
    )


def test_discovery_prerequisites_are_executable_locally(tmp_path: Path) -> None:
    skill_doc = _read("SKILL.md")

    assert _frontmatter_value(skill_doc, "name") == "delivery-flow"

    skills_dir = tmp_path / ".codex" / "skills"
    skills_dir.mkdir(parents=True)
    install_path = skills_dir / "delivery-flow"
    install_path.symlink_to(REPO_ROOT, target_is_directory=True)

    assert install_path.is_symlink()
    assert (install_path / "SKILL.md").is_file()


def test_activation_prerequisites_align_skill_metadata_with_documented_trigger_paths() -> None:
    skill_doc = _read("SKILL.md")
    codex_doc = _read("docs/README.codex.md")
    codex_doc_zh = _read("docs/README.codex.zh-CN.md")

    assert _frontmatter_value(skill_doc, "name") == "delivery-flow"
    assert _frontmatter_value(skill_doc, "description")
    assert "delivery-flow" in _normalized(codex_doc)
    assert "delivery-flow" in _normalized(codex_doc_zh)
    _assert_matches(codex_doc, r"(delivery-flow.{0,80}(by name|mention)|(by name|mention).{0,80}delivery-flow)")
    _assert_matches(codex_doc, r"(task.{0,80}(match|description)|(match|description).{0,80}task)")
    _assert_matches(codex_doc_zh, r"(delivery-flow.{0,20}(提到|提及|名称)|(提到|提及|名称).{0,20}delivery-flow)")
    _assert_matches(codex_doc_zh, r"(任务.{0,40}(描述|触发|命中)|(描述|触发|命中).{0,40}任务)")


def test_pass_path_preserves_expected_owner_facing_contract_in_both_modes() -> None:
    backed_result = _run_mode(
        has_superpowers=True,
        review_results=[{"raw_result": "approved"}, {"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )
    fallback_result = _run_mode(
        has_superpowers=False,
        review_results=[{"raw_result": "approved"}, {"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )

    assert backed_result.mode == "superpowers-backed"
    assert fallback_result.mode == "fallback"
    assert backed_result.stop_reason is StopReason.PASS
    assert fallback_result.stop_reason is StopReason.PASS
    assert backed_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert fallback_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert backed_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert fallback_result.stage_sequence == backed_result.stage_sequence
    assert backed_result.completed_task_ids == ["task-1", "task-2"]
    assert fallback_result.completed_task_ids == ["task-1", "task-2"]
    assert backed_result.pending_task_id is None
    assert fallback_result.pending_task_id is None
    assert backed_result.open_issue_summaries == []
    assert fallback_result.open_issue_summaries == []
    assert backed_result.owner_acceptance_required is False
    assert fallback_result.owner_acceptance_required is False
    assert "completed tasks: task-1, task-2" in backed_result.final_summary
    assert "completed tasks: task-1, task-2" in fallback_result.final_summary
    assert "open issues: none" in backed_result.final_summary
    assert "open issues: none" in fallback_result.final_summary
    assert "owner acceptance required: no" in backed_result.final_summary
    assert "owner acceptance required: no" in fallback_result.final_summary
    assert _summary_without_mode_line(backed_result.final_summary) == _summary_without_mode_line(
        fallback_result.final_summary
    )


def test_strict_pass_issues_force_fix_review_before_advancing_in_both_modes() -> None:
    review_results = [
        {
            "raw_result": "approved",
            "required_changes": ["rename helper"],
            "testing_issues": ["add regression test"],
            "maintainability_issues": ["remove duplicate branch"],
        },
        {"raw_result": "approved"},
        {"raw_result": "approved"},
    ]

    backed_result = _run_mode(
        has_superpowers=True,
        review_results=review_results,
        finalize_result={"owner_acceptance_required": False},
    )
    fallback_result = _run_mode(
        has_superpowers=False,
        review_results=review_results,
        finalize_result={"owner_acceptance_required": False},
    )

    assert backed_result.stop_reason is StopReason.PASS
    assert fallback_result.stop_reason is StopReason.PASS
    assert backed_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_fix",
        "running_review",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert fallback_result.stage_sequence == backed_result.stage_sequence
    assert backed_result.completed_task_ids == ["task-1", "task-2"]
    assert fallback_result.completed_task_ids == ["task-1", "task-2"]
    assert "waiting for the owner's next instruction" in backed_result.final_summary
    assert "waiting for the owner's next instruction" in fallback_result.final_summary


def test_owner_decision_path_preserves_expected_owner_facing_contract_in_both_modes() -> None:
    review_results = [
        {"raw_result": "approved"},
        {
            "raw_result": "owner_input_required",
            "findings": ["choose rollout order"],
            "owner_decision_reason": "choose rollout order",
        },
    ]

    backed_result = _run_mode(has_superpowers=True, review_results=review_results)
    fallback_result = _run_mode(has_superpowers=False, review_results=review_results)

    assert backed_result.mode == "superpowers-backed"
    assert fallback_result.mode == "fallback"
    assert backed_result.stop_reason is StopReason.NEEDS_OWNER_DECISION
    assert fallback_result.stop_reason is StopReason.NEEDS_OWNER_DECISION
    assert backed_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert fallback_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert backed_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_dev",
        "running_review",
        "waiting_for_owner",
    ]
    assert fallback_result.stage_sequence == backed_result.stage_sequence
    assert backed_result.completed_task_ids == ["task-1"]
    assert fallback_result.completed_task_ids == ["task-1"]
    assert backed_result.pending_task_id == "task-2"
    assert fallback_result.pending_task_id == "task-2"
    assert backed_result.open_issue_summaries == ["choose rollout order"]
    assert fallback_result.open_issue_summaries == ["choose rollout order"]
    assert backed_result.owner_acceptance_required is True
    assert fallback_result.owner_acceptance_required is True
    assert "completed tasks: task-1" in backed_result.final_summary
    assert "completed tasks: task-1" in fallback_result.final_summary
    assert "open issues: choose rollout order" in backed_result.final_summary
    assert "open issues: choose rollout order" in fallback_result.final_summary
    assert "owner acceptance required: yes" in backed_result.final_summary
    assert "owner acceptance required: yes" in fallback_result.final_summary
    assert "owner decision: choose rollout order" in backed_result.final_summary
    assert "owner decision: choose rollout order" in fallback_result.final_summary
    assert _summary_without_mode_line(backed_result.final_summary) == _summary_without_mode_line(
        fallback_result.final_summary
    )


def test_resume_review_path_preserves_expected_owner_facing_contract_in_both_modes() -> None:
    backed_result = _resume_mode(
        has_superpowers=True,
        review_results=[{"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )
    fallback_result = _resume_mode(
        has_superpowers=False,
        review_results=[{"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )

    assert backed_result.mode == "superpowers-backed"
    assert fallback_result.mode == "fallback"
    assert backed_result.stop_reason is StopReason.PASS
    assert fallback_result.stop_reason is StopReason.PASS
    assert backed_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert fallback_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert backed_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_dev",
        "running_review",
        "waiting_for_owner",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert fallback_result.stage_sequence == backed_result.stage_sequence
    assert backed_result.completed_task_ids == ["task-1", "task-2"]
    assert fallback_result.completed_task_ids == ["task-1", "task-2"]
    assert backed_result.pending_task_id is None
    assert fallback_result.pending_task_id is None
    assert backed_result.open_issue_summaries == []
    assert fallback_result.open_issue_summaries == []
    assert backed_result.owner_acceptance_required is False
    assert fallback_result.owner_acceptance_required is False
    assert "completed tasks: task-1, task-2" in backed_result.final_summary
    assert "completed tasks: task-1, task-2" in fallback_result.final_summary
    assert "open issues: none" in backed_result.final_summary
    assert "open issues: none" in fallback_result.final_summary
    assert "owner acceptance required: no" in backed_result.final_summary
    assert "owner acceptance required: no" in fallback_result.final_summary
    assert "resume: task=task-2 target=running_review" in backed_result.final_summary
    assert "resume: task=task-2 target=running_review" in fallback_result.final_summary
    assert "orchestration:" in _mode_line(backed_result.final_summary)
    assert "orchestration:" not in _mode_line(fallback_result.final_summary)
    assert "orchestration:" not in _summary_without_mode_line(backed_result.final_summary)
    assert "orchestration:" not in _summary_without_mode_line(fallback_result.final_summary)
    assert _summary_without_mode_line(backed_result.final_summary) == _summary_without_mode_line(
        fallback_result.final_summary
    )


def test_resume_dev_restart_preserves_expected_owner_facing_contract_in_both_modes() -> None:
    backed_result = _resume_mode(
        has_superpowers=True,
        review_results=[{"raw_result": "approved"}],
        restart_current_task_from_dev=True,
        finalize_result={"owner_acceptance_required": False},
    )
    fallback_result = _resume_mode(
        has_superpowers=False,
        review_results=[{"raw_result": "approved"}],
        restart_current_task_from_dev=True,
        finalize_result={"owner_acceptance_required": False},
    )

    assert backed_result.mode == "superpowers-backed"
    assert fallback_result.mode == "fallback"
    assert backed_result.stop_reason is StopReason.PASS
    assert fallback_result.stop_reason is StopReason.PASS
    assert backed_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert fallback_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert backed_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_dev",
        "running_review",
        "waiting_for_owner",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert fallback_result.stage_sequence == backed_result.stage_sequence
    assert backed_result.completed_task_ids == ["task-1", "task-2"]
    assert fallback_result.completed_task_ids == ["task-1", "task-2"]
    assert backed_result.pending_task_id is None
    assert fallback_result.pending_task_id is None
    assert backed_result.open_issue_summaries == []
    assert fallback_result.open_issue_summaries == []
    assert backed_result.owner_acceptance_required is False
    assert fallback_result.owner_acceptance_required is False
    assert "completed tasks: task-1, task-2" in backed_result.final_summary
    assert "completed tasks: task-1, task-2" in fallback_result.final_summary
    assert "open issues: none" in backed_result.final_summary
    assert "open issues: none" in fallback_result.final_summary
    assert "owner acceptance required: no" in backed_result.final_summary
    assert "owner acceptance required: no" in fallback_result.final_summary
    assert "resume: task=task-2 target=running_dev" in backed_result.final_summary
    assert "resume: task=task-2 target=running_dev" in fallback_result.final_summary
    assert "orchestration:" in _mode_line(backed_result.final_summary)
    assert "orchestration:" not in _mode_line(fallback_result.final_summary)
    assert "orchestration:" not in _summary_without_mode_line(backed_result.final_summary)
    assert "orchestration:" not in _summary_without_mode_line(fallback_result.final_summary)
    assert _summary_without_mode_line(backed_result.final_summary) == _summary_without_mode_line(
        fallback_result.final_summary
    )
