from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from delivery_flow.controller import run_delivery_flow
from delivery_flow.contracts import TaskExecutionContext
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


def _quoted_examples(document: str) -> list[str]:
    return re.findall(r'"([^"\n]+)"', document)


def _description_trigger_signals(*, task_prompt: str, skill_description: str) -> set[str]:
    prompt = task_prompt.lower()
    description = skill_description.lower()
    signals: set[str] = set()
    if "dev/review/fix" in description and all(token in prompt for token in ("dev", "review", "fix")):
        signals.add("workflow")
    if "owner input is required" in description and "owner input is required" in prompt:
        signals.add("stop_condition")
    return signals


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
            "summary": "skill validation program",
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
        payload={"ticket": 301, "goal": "skill validation"},
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
    skill_name = _frontmatter_value(skill_doc, "name")
    description = _frontmatter_value(skill_doc, "description")
    quoted_examples = _quoted_examples(codex_doc)

    assert description
    assert skill_name in codex_doc
    assert quoted_examples
    assert any(skill_name in example for example in quoted_examples)
    observed_signals = set().union(
        *(
            _description_trigger_signals(
                task_prompt=example,
                skill_description=description,
            )
            for example in quoted_examples
        )
    )
    assert observed_signals == {"workflow", "stop_condition"}
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
