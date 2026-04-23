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
        "codex is discovery-only",
        "discovery-only",
        "does not inject a session-start bootstrap",
        "no session-start bootstrap parity",
        "docs/ is human-facing",
        "skills/ is agent-facing",
        "bootstrap-capable platforms",
        "claude code",
        "cursor",
        "opencode",
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
        "codex is discovery-only",
        "discovery-only",
        "does not inject a session-start bootstrap",
        "no session-start bootstrap parity",
        "bootstrap-capable platforms",
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
        "bootstrap-capable",
        "before any response",
        "ongoing delivery thread",
        "plan presence alone is not enough to yield",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
        "yield only when the request is truly single-phase",
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
        "bootstrap-capable",
        "before any response",
        "review/fix continuation is a strong signal",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
        "single-phase work should yield",
        "config hook",
        "experimental.chat.system.transform",
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
        "skills/ is agent-facing",
        "codex is discovery-only",
        "no session-start bootstrap parity",
        "claude code, cursor, and opencode are bootstrap-capable",
        "skill selection guide",
        "common mis-selection patterns",
        "discovery-only",
        "bootstrap-capable",
        "claude/cursor/opencode",
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
        "skills/ 是给 agent 读取的",
        "codex is discovery-only",
        "没有 session-start bootstrap parity",
        "claude code, cursor, and opencode are bootstrap-capable",
        "技能选择指南",
        "常见误选模式",
        "discovery-only",
        "bootstrap-capable",
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


def test_codex_docs_describe_discovery_mode_without_bootstrap_parity() -> None:
    codex_doc = _read("docs/platforms/codex.md")
    codex_doc_zh = _read("docs/platforms/codex.zh-CN.md")

    _assert_mentions(
        codex_doc,
        "capability model",
        "codex is discovery-only",
        "discovery-only",
        "does not inject a session-start bootstrap",
        "no session-start bootstrap parity",
        "bootstrap-capable platforms",
        "codex cannot claim that parity until a real bootstrap surface exists",
    )

    _assert_mentions(
        codex_doc_zh,
        "能力模型",
        "codex is discovery-only",
        "discovery-only",
        "不会注入 session-start bootstrap",
        "没有 session-start bootstrap parity",
        "bootstrap-capable",
        "不能声称具备同等能力",
    )


def test_bootstrap_capable_platform_docs_describe_strong_root_routing_contract() -> None:
    claude_doc = _read("docs/platforms/claude.md")
    opencode_doc = _read("docs/platforms/opencode.md")

    _assert_mentions(
        claude_doc,
        "bootstrap-capable",
        "before any response",
        "ongoing delivery thread",
        "plan presence alone is not enough to yield",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
        "yield only when the request is truly single-phase",
    )
    _assert_mentions(
        opencode_doc,
        "bootstrap-capable",
        "before any response",
        "review/fix continuation is a strong signal",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
        "single-phase work should yield",
    )


def test_platform_docs_have_zh_cn_parity() -> None:
    readme_codex_zh = _read("docs/platforms/codex.zh-CN.md")
    readme_claude_zh = _read("docs/platforms/claude.zh-CN.md")
    readme_opencode_zh = _read("docs/platforms/opencode.zh-CN.md")

    _assert_mentions(
        readme_codex_zh,
        "using-delivery-flow",
        "原生 skill discovery",
        "codex is discovery-only",
        "discovery-only",
        "没有 session-start bootstrap parity",
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
        "bootstrap-capable",
        "before any response",
        "ongoing delivery thread",
        "plan presence alone is not enough to yield",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
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
        "bootstrap-capable",
        "before any response",
        "review/fix continuation is a strong signal",
        "root-routing bootstrap",
        "strong root-routing bootstrap",
        "take ownership",
        "on each new user turn",
        "single-phase work should yield",
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
    assert (REPO_ROOT / "skills" / "delivery-flow" / "superpowers-backed.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "fallback.md").is_file()
    assert (REPO_ROOT / "skills" / "delivery-flow" / "verification-scenarios.md").is_file()
