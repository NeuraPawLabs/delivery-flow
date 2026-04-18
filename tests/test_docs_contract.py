from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _assert_verification_markers(doc: str, *, success_marker: str, tests_pass_marker: str) -> None:
    assert "uv run pytest" in doc
    assert success_marker in doc
    assert tests_pass_marker in doc


def test_skill_doc_describes_skill_centered_task_loop_contract() -> None:
    skill_doc = _read("SKILL.md")

    assert "Use this skill when one main agent should keep work moving through:" in skill_doc
    assert "task-by-task `dev -> review -> fix -> review ...`" in skill_doc
    assert "review results normalize to exactly:" in skill_doc
    assert "terminal states always return control to the owner and wait" in skill_doc
    assert "Silent fallback is forbidden." in skill_doc


def test_codex_install_docs_cover_discovery_activation_and_current_baseline() -> None:
    install_doc = _read(".codex/INSTALL.md")
    codex_doc = _read("docs/README.codex.md")
    codex_doc_zh = _read("docs/README.codex.zh-CN.md")

    assert "~/.codex/skills/delivery-flow" in install_doc
    assert "`SKILL.md` exists at the linked path" in install_doc
    _assert_verification_markers(
        install_doc,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )

    assert "Codex scans `~/.codex/skills/` at session start" in codex_doc
    assert "you mention `delivery-flow` by name" in codex_doc
    assert "the task matches the `SKILL.md` description" in codex_doc
    _assert_verification_markers(
        codex_doc,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )
    assert "task-by-task dev/review/fix -> finalize -> wait" in codex_doc

    assert "Codex 会在会话启动时扫描 `~/.codex/skills/`" in codex_doc_zh
    assert "你直接提到 `delivery-flow`" in codex_doc_zh
    assert "任务描述命中 `SKILL.md` 里的触发条件" in codex_doc_zh
    _assert_verification_markers(
        codex_doc_zh,
        success_marker="成功完成",
        tests_pass_marker="全部仓库测试通过",
    )
    assert "task-by-task dev/review/fix -> finalize -> wait" in codex_doc_zh


def test_project_readmes_highlight_task_loop_runtime_scope() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")

    assert "task-by-task runtime after planning" in readme
    assert "includes the explicit `running_finalize` stage before `waiting_for_owner`" in readme
    assert "repository verification baseline" in readme
    assert "/home/mm/workdir/code/python/delivery-flow" in readme
    _assert_verification_markers(
        readme,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )

    assert "plan 之后按 task 逐个推进 runtime" in readme_zh
    assert "包含显式的 `running_finalize` 阶段，然后才进入 `waiting_for_owner`" in readme_zh
    assert "当前仓库验证基线" in readme_zh
    assert "/home/mm/workdir/code/python/delivery-flow" in readme_zh
    _assert_verification_markers(
        readme_zh,
        success_marker="成功完成",
        tests_pass_marker="全部仓库测试通过",
    )


def test_readmes_link_skill_validation_matrix() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")

    assert "[docs/skill-validation-matrix.md](./docs/skill-validation-matrix.md)" in readme
    assert "[docs/skill-validation-matrix.md](./docs/skill-validation-matrix.md)" in readme_zh


def test_skill_validation_matrix_exists_and_indexes_repo_backed_evidence() -> None:
    matrix = _read("docs/skill-validation-matrix.md")

    assert "# Skill Validation Matrix" in matrix
    assert "tests/test_skill_validation_program.py" in matrix
    assert "tests/test_docs_contract.py" in matrix
    assert "tests/test_runtime_engine.py" in matrix
    assert "tests/test_controller.py" in matrix
    assert "tests/test_default_use_path.py" in matrix
    assert "docs/stage-2-real-task-validation.md" in matrix


def test_backend_docs_preserve_mode_contract_and_parity_requirements() -> None:
    superpowers_doc = _read("superpowers-backed.md")
    fallback_doc = _read("fallback.md")

    assert "after planning, the main agent dispatches subagents" in superpowers_doc
    assert "it may not redefine:" in superpowers_doc
    assert "verification-unavailable escalation" in superpowers_doc
    assert "The controller must normalize it into:" in superpowers_doc

    assert "Fallback exists to preserve the same owner-facing workflow contract" in fallback_doc
    assert "Fallback may differ internally, but it must preserve:" in fallback_doc
    assert "task-by-task post-plan execution" in fallback_doc
    assert "silently weaken the owner-facing contract" in fallback_doc


def test_verification_scenarios_cover_discovery_activation_compliance_and_parity() -> None:
    scenarios = _read("verification-scenarios.md")

    assert "## Scenario 1: Discovery Works" in scenarios
    assert "expect Codex to discover the skill on a fresh session start" in scenarios
    assert "## Scenario 2: Activation Works" in scenarios
    assert "expect the skill to be selected in both cases" in scenarios
    assert "## Scenario 3: Compliance Contract Holds" in scenarios
    assert "expect the main agent to own workflow transitions" in scenarios
    assert "expect review results to normalize to `pass / blocker / needs_owner_decision`" in scenarios
    assert "## Scenario 8: Fallback Preserves Parity" in scenarios
    assert "expect fallback to preserve stop rules rather than silently weakening them" in scenarios
    assert "expect no silent fallback" in scenarios
