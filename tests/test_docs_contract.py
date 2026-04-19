from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _assert_verification_markers(doc: str, *, success_marker: str, tests_pass_marker: str) -> None:
    assert "uv run pytest" in doc
    assert success_marker in doc
    assert tests_pass_marker in doc


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _assert_mentions(doc: str, *fragments: str) -> None:
    normalized_doc = _normalized(doc)
    for fragment in fragments:
        assert fragment.lower() in normalized_doc


def test_skill_doc_keeps_core_task_loop_contract() -> None:
    skill_doc = _read("SKILL.md")

    _assert_mentions(skill_doc, "name: delivery-flow")
    _assert_mentions(skill_doc, "dev", "review", "fix", "finalize", "wait")
    _assert_mentions(skill_doc, "superpowers-backed", "fallback")
    _assert_mentions(skill_doc, "execution_strategy", "subagent-driven", "inline", "unresolved")
    _assert_mentions(skill_doc, "pass", "needs_owner_decision")
    _assert_mentions(
        skill_doc,
        "required changes",
        "testing issues",
        "maintainability issues",
    )
    _assert_mentions(skill_doc, "owner", "terminal", "subagents")
    _assert_mentions(
        skill_doc,
        "may ask once after planning",
        "must not ask again",
        "owner explicitly changes strategy",
        "must not reopen execution-strategy selection",
    )


def test_backend_docs_keep_mode_and_review_smoke() -> None:
    superpowers_doc = _read("superpowers-backed.md")
    fallback_doc = _read("fallback.md")

    _assert_mentions(superpowers_doc, "superpowers", "dev", "review", "fix", "subagents")
    _assert_mentions(superpowers_doc, "normalized", "pass", "blocker", "needs_owner_decision")
    _assert_mentions(
        superpowers_doc,
        "execution_strategy=unresolved",
        "may ask once after planning",
        "must not re-open that choice",
        "owner explicitly changes strategy mid-run",
        "execution_strategy=inline",
        "current session",
    )
    _assert_mentions(fallback_doc, "fallback", "dev", "review", "fix", "natively")
    _assert_mentions(
        fallback_doc,
        "strict pass requirements",
        "normalized review results",
        "exactly",
        "pass",
        "blocker",
        "needs_owner_decision",
    )
    _assert_mentions(
        fallback_doc,
        "execution_strategy=unresolved",
        "may ask once after planning",
        "must not re-open that choice",
        "owner explicitly changes strategy mid-run",
    )


def test_codex_install_docs_cover_discovery_install_and_verification() -> None:
    install_doc = _read(".codex/INSTALL.md")

    _assert_mentions(install_doc, "delivery-flow", ".codex/skills", "skill.md")
    _assert_verification_markers(
        install_doc,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )


def test_project_readmes_cover_current_machine_install_and_verification() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")

    _assert_mentions(readme, "delivery-flow", "spec", "plan", "dev", "review", "fix")
    _assert_mentions(readme, "superpowers-backed", "fallback", "subagents")
    _assert_mentions(readme, "execution_strategy", "subagent-driven", "inline", "unresolved")
    _assert_mentions(
        readme,
        "may ask once after planning",
        "must not reopen a generic execution-choice prompt",
        "owner can explicitly change execution strategy mid-run",
        "upstream generic templates must not override a determined strategy",
    )
    _assert_mentions(
        readme,
        "owner explicit instruction",
        "active run state",
        "repository-local preset",
        "delivery-flow default",
        "upstream generic behavior",
        "current session",
    )
    _assert_mentions(readme, "required changes", "testing issues", "maintainability issues")
    _assert_verification_markers(
        readme,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )

    _assert_mentions(readme_zh, "delivery-flow", "spec", "plan", "dev", "review", "fix")
    _assert_mentions(readme_zh, "superpowers-backed", "fallback", "subagents")
    _assert_mentions(readme_zh, "execution_strategy", "subagent-driven", "inline", "unresolved")
    _assert_mentions(
        readme_zh,
        "询问一次",
        "不会再次打开通用执行方式选择",
        "显式修改 execution strategy",
        "上游通用模板不得覆盖已确定的 strategy",
    )
    _assert_mentions(
        readme_zh,
        "owner explicit instruction",
        "active run state",
        "repository-local preset",
        "delivery-flow default",
        "upstream generic behavior",
        "当前会话内执行",
    )
    _assert_mentions(readme_zh, "required changes", "testing issues", "maintainability issues")
    _assert_verification_markers(
        readme_zh,
        success_marker="成功完成",
        tests_pass_marker="全部仓库测试通过",
    )


def test_codex_guides_lock_execution_strategy_contract() -> None:
    codex_doc = _read("docs/README.codex.md")
    codex_doc_zh = _read("docs/README.codex.zh-CN.md")

    _assert_mentions(codex_doc, "execution strategy", "subagent-driven", "inline", "unresolved")
    _assert_mentions(
        codex_doc,
        "may ask once after planning",
        "already determined",
        "without reopening a generic execution-choice prompt",
        "owner explicitly changes execution strategy mid-run",
        "upstream generic templates do not override the determined strategy",
        "owner explicit instruction",
        "active run state",
        "repository-local preset",
        "delivery-flow default",
        "upstream generic behavior",
        "current session",
    )
    _assert_mentions(codex_doc, "strict `pass` rejects unresolved required changes")

    _assert_mentions(codex_doc_zh, "execution strategy", "subagent-driven", "inline", "unresolved")
    _assert_mentions(
        codex_doc_zh,
        "询问一次",
        "已经确定",
        "不会再次打开通用执行方式选择",
        "显式修改 execution strategy",
        "上游通用模板不得覆盖已确定的 strategy",
        "owner explicit instruction",
        "active run state",
        "repository-local preset",
        "delivery-flow default",
        "upstream generic behavior",
        "当前会话内执行",
    )
    _assert_mentions(codex_doc_zh, "严格 `pass` 会拒绝 unresolved required changes")


def test_verification_scenarios_cover_execution_strategy_edges() -> None:
    scenarios_doc = _read("verification-scenarios.md")

    _assert_mentions(
        scenarios_doc,
        "execution strategy",
        "one post-plan execution-strategy question",
        "no repeated execution-choice question",
        "generic upstream planning templates not to override the determined strategy",
        "owner explicitly changes it during the active run",
        "next schedulable task",
        "owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior",
        "superpowers-backed",
        "inline",
    )
