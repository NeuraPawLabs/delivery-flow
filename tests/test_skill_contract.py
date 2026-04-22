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


def _section_bounds(document: str, heading: str) -> tuple[int, int]:
    pattern = rf"^## {re.escape(heading)}\n"
    match = re.search(pattern, document, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"Missing section: {heading}")

    start = match.start()
    next_heading = re.search(r"^## ", document[match.end() :], flags=re.MULTILINE)
    end = len(document) if next_heading is None else match.end() + next_heading.start()
    return start, end


def _section_body(document: str, heading: str) -> str:
    start, end = _section_bounds(document, heading)
    section = document[start:end]
    lines = section.splitlines()[1:]
    return "\n".join(lines).strip()


def _section_headings(document: str) -> list[str]:
    return re.findall(r"^## (.+)$", document, flags=re.MULTILINE)


def _assert_owner_facing_fields_match(left: RuntimeResult, right: RuntimeResult) -> None:
    assert left.stop_reason is right.stop_reason
    assert left.final_state is right.final_state
    assert left.stage_sequence == right.stage_sequence
    assert left.completed_task_ids == right.completed_task_ids
    assert left.pending_task_id == right.pending_task_id
    assert left.open_issue_summaries == right.open_issue_summaries
    assert left.owner_acceptance_required is right.owner_acceptance_required


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
    skill_doc = _read("skills/delivery-flow/SKILL.md")

    assert _frontmatter_value(skill_doc, "name") == "delivery-flow"

    skills_dir = tmp_path / ".agents" / "skills"
    skills_dir.mkdir(parents=True)
    install_path = skills_dir / "delivery-flow"
    install_path.symlink_to(REPO_ROOT / "skills", target_is_directory=True)

    assert install_path.is_symlink()
    assert (install_path / "delivery-flow" / "SKILL.md").is_file()
    assert (install_path / "using-delivery-flow" / "SKILL.md").is_file()


def test_activation_prerequisites_align_skill_metadata_with_documented_trigger_paths() -> None:
    skill_doc = _read("skills/delivery-flow/SKILL.md")
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


def test_skill_frontmatter_declares_top_level_process_role_for_ongoing_delivery_threads() -> None:
    description = _normalized(_frontmatter_value(_read("skills/delivery-flow/SKILL.md"), "description"))

    assert "top-level process skill" in description
    assert "ongoing delivery thread" in description
    assert "each new user turn" in description


def test_skill_frontmatter_declares_existing_plan_and_review_feedback_do_not_disqualify_delivery_flow() -> None:
    description = _normalized(_frontmatter_value(_read("skills/delivery-flow/SKILL.md"), "description"))

    assert "even if a plan already exists" in description
    assert "review feedback" in description
    assert "yield when only a single phase is needed" in description


def test_skill_frontmatter_declares_neighbor_skills_as_stage_specific_or_subordinate() -> None:
    description = _normalized(_frontmatter_value(_read("skills/delivery-flow/SKILL.md"), "description"))

    assert "stage-specific or subordinate" in description
    assert "receiving-code-review" in description
    assert "writing-plans" in description
    assert "executing-plans" in description
    assert "test-driven-development" in description


def test_shared_skill_surface_exists() -> None:
    assert (REPO_ROOT / "skills" / "delivery-flow" / "SKILL.md").is_file()
    assert (REPO_ROOT / "skills" / "using-delivery-flow" / "SKILL.md").is_file()


def test_codex_shared_install_surface_exposes_both_skills(tmp_path: Path) -> None:
    install_root = tmp_path / ".agents" / "skills"
    install_root.mkdir(parents=True)
    install_path = install_root / "delivery-flow"
    install_path.symlink_to(REPO_ROOT / "skills", target_is_directory=True)

    assert install_path.is_symlink()
    assert (install_path / "delivery-flow" / "SKILL.md").is_file()
    assert (install_path / "using-delivery-flow" / "SKILL.md").is_file()


def test_root_skill_entrypoint_is_removed() -> None:
    assert not (REPO_ROOT / "SKILL.md").exists()


def test_using_delivery_flow_is_a_root_routing_skill() -> None:
    routing_doc = _read("skills/using-delivery-flow/SKILL.md")
    description = _normalized(_frontmatter_value(routing_doc, "description"))

    assert _frontmatter_value(routing_doc, "name") == "using-delivery-flow"
    assert "starting a conversation" in description
    assert "continuing an ongoing delivery thread" in description
    assert "delivery-flow" in description
    assert "single-phase" in description

    body = _normalized(routing_doc)
    for marker in (
        "thin routing skill",
        "route into `delivery-flow`",
        "yield to the normal stage-specific skills",
        "do not duplicate `delivery-flow` execution semantics",
    ):
        assert marker in body


def test_skill_doc_declares_selection_priority_and_neighbor_skill_markers() -> None:
    selection_priority = _section_body(_read("skills/delivery-flow/SKILL.md"), "Selection Priority")
    relationship = _section_body(_read("skills/delivery-flow/SKILL.md"), "Relationship To Other Process Skills")

    for marker in (
        "top-level orchestrator for an ongoing delivery thread",
        "prefer `delivery-flow` over `executing-plans`",
        "existing plan presence alone is not enough",
        "review/fix continuation",
    ):
        assert marker in selection_priority

    for marker in (
        "`brainstorming`",
        "`writing-plans`",
        "`executing-plans`",
        "stage-specific or subordinate workflows relative to `delivery-flow`",
    ):
        assert marker in relationship


def test_skill_doc_declares_routing_contract_via_sections_and_markers() -> None:
    skill_doc = _read("skills/delivery-flow/SKILL.md")
    routing_decision = _section_body(skill_doc, "Routing Decision")
    when_to_take_ownership = _section_body(skill_doc, "When To Take Ownership")
    when_to_yield = _section_body(skill_doc, "When To Yield")
    use_it_when = _section_body(skill_doc, "Use It When")

    for marker in (
        "router-first",
        "routing decision",
        "re-evaluate routing on each new user turn",
        "do not re-route on every internal phase boundary",
    ):
        assert marker in _normalized(skill_doc)

    for marker in (
        "take ownership as the top-level orchestrator",
        "yield to the normal skill ecosystem",
    ):
        assert marker in routing_decision

    assert "a plan already exists" in when_to_take_ownership
    assert "review feedback has arrived" in when_to_take_ownership
    assert "only a single phase is needed" in when_to_yield
    assert "task by task" in use_it_when


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
