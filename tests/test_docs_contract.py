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
    _assert_mentions(skill_doc, "pass", "needs_owner_decision")
    _assert_mentions(
        skill_doc,
        "required changes",
        "testing issues",
        "maintainability issues",
    )
    _assert_mentions(skill_doc, "owner", "terminal", "subagents")


def test_backend_docs_keep_mode_and_review_smoke() -> None:
    superpowers_doc = _read("superpowers-backed.md")
    fallback_doc = _read("fallback.md")

    _assert_mentions(superpowers_doc, "superpowers", "dev", "review", "fix", "subagents")
    _assert_mentions(superpowers_doc, "normalized", "pass", "blocker", "needs_owner_decision")
    _assert_mentions(fallback_doc, "fallback", "dev", "review", "fix", "natively")
    _assert_mentions(fallback_doc, "strict pass requirements", "normalized review results")


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
    _assert_mentions(readme, "required changes", "testing issues", "maintainability issues")
    _assert_verification_markers(
        readme,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )

    _assert_mentions(readme_zh, "delivery-flow", "spec", "plan", "dev", "review", "fix")
    _assert_mentions(readme_zh, "superpowers-backed", "fallback", "subagents")
    _assert_mentions(readme_zh, "required changes", "testing issues", "maintainability issues")
    _assert_verification_markers(
        readme_zh,
        success_marker="成功完成",
        tests_pass_marker="全部仓库测试通过",
    )
