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


def _assert_markdown_link(doc: str, target: str) -> None:
    pattern = re.compile(rf"\[[^\]]+\]\({re.escape(target)}\)", re.IGNORECASE)
    assert pattern.search(doc)


def test_skill_doc_keeps_core_task_loop_contract() -> None:
    skill_doc = _read("skills/delivery-flow/SKILL.md")

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
    superpowers_doc = _read("skills/delivery-flow/superpowers-backed.md")
    fallback_doc = _read("skills/delivery-flow/fallback.md")

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

    _assert_mentions(
        install_doc,
        "delivery-flow",
        "~/.agents/skills",
        "skills/delivery-flow",
        "skills/using-delivery-flow",
        "`uv` for local verification",
        "https://github.com/neurapawlabs/delivery-flow.git",
        "windows",
        "mklink /j",
        "powershell",
    )
    _assert_verification_markers(
        install_doc,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )


def test_platform_docs_cover_bootstrap_install_paths() -> None:
    codex_install = _read(".codex/INSTALL.md")
    readme_codex = _read("docs/platforms/codex.md")
    readme_claude = _read("docs/platforms/claude.md")
    readme_opencode = _read("docs/platforms/opencode.md")

    _assert_mentions(
        codex_install,
        "~/.agents/skills",
        "skills/delivery-flow",
        "skills/using-delivery-flow",
    )
    _assert_mentions(
        readme_codex,
        "native skill discovery",
        "using-delivery-flow",
        "restart codex",
        "windows powershell",
        "test-path",
        "get-item",
        "fetch and follow instructions from https://raw.githubusercontent.com/neurapawlabs/delivery-flow/main/.codex/install.md",
    )
    _assert_mentions(
        readme_claude,
        "sessionstart",
        ".claude-plugin",
        ".cursor-plugin",
        "bootstrap",
        "routing-only",
        "install this repository as the plugin package",
        "repository root is the install surface",
        "skills/",
        "does not replace the `delivery-flow` skill contract",
        "ongoing delivery threads can prefer `delivery-flow`",
    )
    _assert_mentions(
        readme_opencode,
        "plugin",
        "skills/",
        "directory",
        "using-delivery-flow",
        "bootstrap",
        "routing-only",
        "config hook",
        "experimental.chat.system.transform",
    )


def test_selection_contract_doc_locks_selection_precedence_rules() -> None:
    selection_doc = _read("skills/delivery-flow/selection-contract.md")

    _assert_mentions(
        selection_doc,
        "top-level orchestrator",
        "even if a plan already exists",
        "ongoing delivery thread",
        "prefer `delivery-flow` over `executing-plans`",
        "review/fix continuation",
        "do not switch away merely because planning is complete",
        "brainstorming",
        "writing-plans",
        "executing-plans",
        "subordinate workflows",
    )


def test_router_contract_docs_lock_router_first_take_ownership_and_yield_rules() -> None:
    router_doc = _read("skills/delivery-flow/router-contract.md")

    _assert_mentions(
        router_doc,
        "router-first",
        "take ownership",
        "yield",
        "each new user turn",
        "do not re-route on every internal phase boundary",
        "ongoing delivery thread",
        "single phase",
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
    _assert_mentions(
        readme,
        "human docs",
        "ai skill files",
        "docs/ is human-facing",
        "skills/ contains the ai-facing skill entrypoints",
        "skill selection guide",
        "common mis-selection patterns",
        "even if a plan already exists",
        "prefer `delivery-flow` over `executing-plans`",
        "ongoing delivery thread",
        "review/fix continuation",
        "top-level orchestrator",
        "router-first",
        "each new user turn",
        "take ownership",
        "yield",
    )
    _assert_markdown_link(readme, "./docs/platforms/codex.md")
    _assert_markdown_link(readme, "./docs/platforms/claude.md")
    _assert_markdown_link(readme, "./docs/platforms/opencode.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/selection-contract.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/router-contract.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/superpowers-backed.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/fallback.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/verification-scenarios.md")
    _assert_markdown_link(readme, "./skills/delivery-flow/SKILL.md")
    _assert_markdown_link(readme, "./skills/using-delivery-flow/SKILL.md")
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
    _assert_mentions(
        readme_zh,
        "人类文档",
        "ai skill 文件",
        "docs/ 只放给人类看的文档",
        "skills/ 存放给 agent 读取的 skill 入口",
        "技能选择指南",
        "常见误选模式",
        "即使已经有 plan",
        "优先 delivery-flow",
        "持续交付线程",
        "review/fix",
        "顶层 orchestrator",
        "router-first",
        "每个新的用户回合",
        "接管",
        "让行",
    )
    _assert_markdown_link(readme_zh, "./docs/platforms/codex.zh-CN.md")
    _assert_markdown_link(readme_zh, "./docs/platforms/claude.zh-CN.md")
    _assert_markdown_link(readme_zh, "./docs/platforms/opencode.zh-CN.md")
    _assert_markdown_link(readme_zh, "./skills/delivery-flow/superpowers-backed.md")
    _assert_markdown_link(readme_zh, "./skills/delivery-flow/fallback.md")
    _assert_markdown_link(readme_zh, "./skills/delivery-flow/verification-scenarios.md")
    _assert_markdown_link(readme_zh, "./skills/delivery-flow/SKILL.md")
    _assert_markdown_link(readme_zh, "./skills/using-delivery-flow/SKILL.md")
    _assert_mentions(readme_zh, "required changes", "testing issues", "maintainability issues")
    _assert_verification_markers(
        readme_zh,
        success_marker="成功完成",
        tests_pass_marker="全部仓库测试通过",
    )


def test_codex_guides_lock_execution_strategy_contract() -> None:
    codex_doc = _read("docs/platforms/codex.md")
    codex_doc_zh = _read("docs/platforms/codex.zh-CN.md")

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
    _assert_mentions(
        codex_doc,
        "when delivery-flow should win over executing-plans",
        "why plan existence alone is not enough",
        "how delivery-flow relates to brainstorming and writing-plans",
        "top-level orchestrator",
        "ongoing delivery thread",
        "review/fix continuation",
        "router-first",
        "each new user turn",
        "yield",
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
    _assert_mentions(
        codex_doc_zh,
        "何时 delivery-flow 应优先于 executing-plans",
        "为什么仅有 plan 并不足够",
        "delivery-flow 与 brainstorming 和 writing-plans 的关系",
        "顶层 orchestrator",
        "持续交付线程",
        "review/fix",
        "router-first",
        "每个新的用户回合",
        "让行",
    )
    _assert_mentions(codex_doc_zh, "严格 `pass` 会拒绝 unresolved required changes")


def test_platform_docs_have_zh_cn_parity() -> None:
    readme_codex_zh = _read("docs/platforms/codex.zh-CN.md")
    readme_claude_zh = _read("docs/platforms/claude.zh-CN.md")
    readme_opencode_zh = _read("docs/platforms/opencode.zh-CN.md")

    _assert_mentions(
        readme_codex_zh,
        "using-delivery-flow",
        "原生 skill discovery",
        "windows powershell",
        "test-path",
        "get-item",
    )
    _assert_mentions(
        readme_claude_zh,
        "sessionstart",
        ".claude-plugin",
        ".cursor-plugin",
        "bootstrap",
        "routing-only",
        "整个仓库作为插件包安装",
        "仓库根目录本身就是 claude code 和 cursor 的安装面",
        "skills/",
        "不会替代 `delivery-flow` 的 skill contract",
        "持续交付线程优先进入 `delivery-flow`",
    )
    _assert_mentions(
        readme_opencode_zh,
        "plugin",
        "skills/",
        "目录",
        "using-delivery-flow",
        "bootstrap",
        "routing-only",
        "config hook",
        "experimental.chat.system.transform",
    )


def test_verification_scenarios_cover_execution_strategy_edges() -> None:
    scenarios_doc = _read("skills/delivery-flow/verification-scenarios.md")

    _assert_mentions(
        scenarios_doc,
        "~/.agents/skills/delivery-flow",
        "delivery-flow/skill.md",
        "using-delivery-flow/skill.md",
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
    _assert_mentions(
        scenarios_doc,
        "existing plan but ongoing delivery thread",
        "top-level workflow controller",
        "plan presence alone does not select executing-plans",
        "delivery-flow precedence",
        "brainstorming completes but delivery flow owns the thread",
        "post-plan orchestration",
        "review feedback arrives mid-execution",
        "stay inside `delivery-flow`",
        "new feature, no ongoing thread",
        "yield",
        "next user turn",
        "no re-routing on every internal phase boundary",
    )


def test_root_markdown_surface_is_readme_only() -> None:
    root_markdown_files = sorted(path.name for path in REPO_ROOT.glob("*.md"))

    assert root_markdown_files == ["README.md", "README.zh-CN.md"]


def test_docs_layout_is_human_only_and_skill_supporting_docs_live_under_skills() -> None:
    assert (REPO_ROOT / "docs" / "platforms" / "codex.md").is_file()
    assert (REPO_ROOT / "docs" / "platforms" / "claude.md").is_file()
    assert (REPO_ROOT / "docs" / "platforms" / "opencode.md").is_file()
    assert not (REPO_ROOT / "docs" / "skills").exists()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "selection-contract.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "router-contract.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "superpowers-backed.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "fallback.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "verification-scenarios.md").is_file()
