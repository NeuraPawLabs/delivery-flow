from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_skill_doc_describes_post_plan_task_loop_and_owner_acceptance() -> None:
    skill_doc = _read("SKILL.md")

    assert "drives `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`" in skill_doc
    assert "task-level `pass` completes the current task and advances to the next planned task" in skill_doc
    assert "the runtime stops with `pass` only after all planned tasks complete and `finalize` runs" in skill_doc
    assert "`owner_acceptance_required` may be `True` or `False` depending on the finalization result" in skill_doc
    assert "The workflow is complete only when:" not in skill_doc
    assert "- normalized review result is `pass`" not in skill_doc


def test_project_readmes_highlight_task_loop_runtime_scope() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")

    assert "task-by-task runtime after planning" in readme
    assert "includes the explicit `running_finalize` stage before `waiting_for_owner`" in readme
    assert "repository verification baseline is `uv run pytest` -> `80 passed`" in readme
    assert "Current baseline: `80 passed`" in readme

    assert "plan 之后按 task 逐个推进 runtime" in readme_zh
    assert "包含显式的 `running_finalize` 阶段，然后才进入 `waiting_for_owner`" in readme_zh
    assert "当前仓库验证基线：`uv run pytest` -> `80 passed`" in readme_zh
    assert "当前基线：`80 passed`" in readme_zh


def test_backend_docs_map_actions_to_task_loop_contract() -> None:
    superpowers_doc = _read("superpowers-backed.md")
    fallback_doc = _read("fallback.md")

    assert "`run_dev` -> implement the current planned task" in superpowers_doc
    assert "`run_review` -> review the current planned task result" in superpowers_doc
    assert "`finalize` -> run once after all planned tasks pass successfully" in superpowers_doc
    assert "terminal stop is summarized" not in superpowers_doc

    assert "`run_dev` -> implement the current planned task natively" in fallback_doc
    assert "`run_review` -> review the current planned task result natively" in fallback_doc
    assert "`finalize` -> run once after all planned tasks pass successfully and emit the same owner-facing closeout contract" in fallback_doc
    assert "after task-loop execution stops" not in fallback_doc


def test_verification_scenarios_cover_task_loop_default_use_and_owner_acceptance() -> None:
    scenarios = _read("verification-scenarios.md")

    assert "expect task 2 to start only after task 1 passes review" in scenarios
    assert "expect `running_finalize` before `waiting_for_owner` on full pass" in scenarios
    assert "expect final summary to surface `owner acceptance required: yes` when owner input is still required" in scenarios
    assert "expect no `running_finalize` when the runtime stops early for `needs_owner_decision`" in scenarios
    assert "expect no `running_finalize` when verification is unavailable mid-task" in scenarios
