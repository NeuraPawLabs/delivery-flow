from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict[str, object]:
    return json.loads(_read(relative_path))


def _run_hook_wrapper(*args: str, **env_updates: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(env_updates)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "hooks" / "run-hook.cmd"), *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )


def _run_session_start(**env_updates: str) -> dict[str, object]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CLAUDE_PLUGIN_ROOT", "COPILOT_CLI", "CURSOR_PLUGIN_ROOT"}
    }
    env.update(env_updates)

    result = subprocess.run(
        [str(REPO_ROOT / "hooks" / "session-start")],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )

    return json.loads(result.stdout)


def _run_node_json(script: str) -> dict[str, object]:
    if shutil.which("node") is None:
        pytest.skip("node is required for OpenCode plugin contract checks")

    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    return json.loads(result.stdout)


def _assert_routing_bootstrap(bootstrap: str) -> None:
    assert "using-delivery-flow" in bootstrap
    assert "ongoing delivery threads" in bootstrap
    assert "routing-focused bootstrap" not in bootstrap
    assert "executing-plans" not in bootstrap
    assert "test-driven-development" not in bootstrap
    assert "brainstorming" not in bootstrap


def _assert_opencode_bootstrap(bootstrap: str) -> None:
    _assert_routing_bootstrap(bootstrap)
    assert "root routing skill" in bootstrap
    assert "routing-only" in bootstrap
    assert "normal skill ecosystem" in bootstrap
    assert "execution semantics" in bootstrap


def test_plugin_manifests_exist_and_keep_expected_fields() -> None:
    claude_manifest = _read_json(".claude-plugin/plugin.json")
    cursor_manifest = _read_json(".cursor-plugin/plugin.json")

    assert claude_manifest["name"] == "delivery-flow"
    assert claude_manifest["description"]
    assert claude_manifest["version"]
    assert claude_manifest["author"]

    assert cursor_manifest["name"] == "delivery-flow"
    assert cursor_manifest["displayName"] == "Delivery Flow"
    assert cursor_manifest["description"]
    assert cursor_manifest["version"]
    assert cursor_manifest["skills"] == "./skills/"
    assert cursor_manifest["hooks"] == "./hooks/hooks-cursor.json"


def test_hook_config_files_keep_expected_schema_and_paths() -> None:
    claude_hooks = _read_json("hooks/hooks.json")
    cursor_hooks = _read_json("hooks/hooks-cursor.json")

    assert claude_hooks == {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start',
                            "async": False,
                        }
                    ],
                }
            ]
        }
    }
    assert cursor_hooks == {
        "version": 1,
        "hooks": {"sessionStart": [{"command": "./hooks/session-start"}]},
    }


def test_session_start_hook_emits_cursor_payload() -> None:
    payload = _run_session_start(CURSOR_PLUGIN_ROOT="C:\\cursor-plugin")

    assert payload.keys() == {"additional_context"}
    _assert_routing_bootstrap(payload["additional_context"])


def test_session_start_hook_emits_claude_payload() -> None:
    payload = _run_session_start(CLAUDE_PLUGIN_ROOT="/tmp/claude-plugin")

    assert payload.keys() == {"hookSpecificOutput"}
    hook_output = payload["hookSpecificOutput"]
    assert isinstance(hook_output, dict)
    assert hook_output.keys() == {"hookEventName", "additionalContext"}
    assert hook_output["hookEventName"] == "SessionStart"
    _assert_routing_bootstrap(hook_output["additionalContext"])


def test_session_start_hook_emits_fallback_payload() -> None:
    payload = _run_session_start()

    assert payload.keys() == {"additionalContext"}
    _assert_routing_bootstrap(payload["additionalContext"])


def test_run_hook_cmd_executes_session_start_on_unix_path() -> None:
    result = _run_hook_wrapper("session-start")
    payload = json.loads(result.stdout)

    assert payload.keys() == {"additionalContext"}
    _assert_routing_bootstrap(payload["additionalContext"])


def test_run_hook_cmd_reports_missing_bash_with_nonzero_exit() -> None:
    wrapper = _read("hooks/run-hook.cmd")

    assert "bash.exe was not found" in wrapper
    assert "exit /b 0" not in wrapper
    assert "exit /b 1" in wrapper


def test_run_hook_cmd_quotes_forwarded_windows_args() -> None:
    wrapper = _read("hooks/run-hook.cmd")

    assert 'set "FORWARDED_ARGS="' in wrapper
    assert 'set "ARG=%~1"' in wrapper
    assert '%ARG:"=\\\\"%' in wrapper
    assert 'set "FORWARDED_ARGS=%FORWARDED_ARGS% "%ARG%""' in wrapper


def test_opencode_package_manifest_points_to_plugin_entry() -> None:
    manifest = _read_json("package.json")

    assert manifest["name"] == "delivery-flow-opencode"
    assert manifest["type"] == "module"
    assert manifest["main"] == ".opencode/plugins/delivery-flow.js"

    exports = manifest["exports"]
    assert isinstance(exports, dict)
    assert exports["."] == "./.opencode/plugins/delivery-flow.js"


def test_opencode_plugin_registers_skills_path_without_mutating_input_config() -> None:
    payload = _run_node_json(
        """
        import fs from "node:fs";
        import path from "node:path";
        import deliveryFlowPlugin from "./.opencode/plugins/delivery-flow.js";

        const hooks = await deliveryFlowPlugin({
          directory: path.resolve("docs"),
          worktree: path.resolve("."),
        });
        const initialConfig = {
          mode: "test",
          skills: {
            paths: ["custom-skill-path"],
            marker: "keep",
          },
        };
        const originalSkills = initialConfig.skills;
        const originalPaths = initialConfig.skills.paths;

        await hooks.config(initialConfig);

        console.log(JSON.stringify({
          config: initialConfig,
          hasRepoSkillsPath: initialConfig.skills.paths.includes(path.resolve("skills")),
          hasRoutingSkillFile: fs.existsSync(path.join(path.resolve("skills"), "using-delivery-flow", "SKILL.md")),
          hasExecutionSkillFile: fs.existsSync(path.join(path.resolve("skills"), "delivery-flow", "SKILL.md")),
          hasConfigHook: typeof hooks.config === "function",
          hasSystemTransformHook: typeof hooks["experimental.chat.system.transform"] === "function",
          sameSkillsObject: initialConfig.skills === originalSkills,
          samePathsArray: initialConfig.skills.paths === originalPaths,
        }));
        """
    )

    config = payload["config"]

    assert config == {
        "mode": "test",
        "skills": {
            "paths": ["custom-skill-path", str(REPO_ROOT / "skills")],
            "marker": "keep",
        },
    }
    assert payload["hasRepoSkillsPath"] is True
    assert payload["hasRoutingSkillFile"] is True
    assert payload["hasExecutionSkillFile"] is True
    assert payload["hasConfigHook"] is True
    assert payload["hasSystemTransformHook"] is True
    assert payload["sameSkillsObject"] is False
    assert payload["samePathsArray"] is False


def test_opencode_plugin_falls_back_to_plugin_repo_root_when_worktree_is_missing() -> None:
    payload = _run_node_json(
        """
        import path from "node:path";
        import deliveryFlowPlugin from "./.opencode/plugins/delivery-flow.js";

        const hooks = await deliveryFlowPlugin({
          directory: path.resolve("docs"),
        });
        const config = {
          skills: {
            paths: [],
          },
        };

        await hooks.config(config);

        console.log(JSON.stringify({
          paths: config.skills.paths,
          repoSkillsPath: path.resolve("skills"),
        }));
        """
    )

    assert payload["paths"] == [payload["repoSkillsPath"]]


def test_opencode_plugin_adds_repo_root_skills_path_when_only_relative_entry_exists() -> None:
    payload = _run_node_json(
        """
        import fs from "node:fs";
        import path from "node:path";
        import deliveryFlowPlugin from "./.opencode/plugins/delivery-flow.js";

        const hooks = await deliveryFlowPlugin({
          directory: path.resolve("docs"),
          worktree: path.resolve("."),
        });
        const config = {
          skills: {
            paths: ["skills"],
          },
        };

        await hooks.config(config);

        console.log(JSON.stringify({
          paths: config.skills.paths,
          repoSkillsPath: path.resolve("skills"),
          hasRoutingSkillFile: fs.existsSync(path.join(path.resolve("skills"), "using-delivery-flow", "SKILL.md")),
        }));
        """
    )

    paths = payload["paths"]
    repo_skills_path = payload["repoSkillsPath"]

    assert isinstance(paths, list)
    assert paths == ["skills", repo_skills_path]
    assert sum(1 for item in paths if item == repo_skills_path) == 1
    assert payload["hasRoutingSkillFile"] is True


def test_opencode_plugin_appends_routing_bootstrap_without_rewriting_existing_string_content() -> None:
    payload = _run_node_json(
        """
        import path from "node:path";
        import deliveryFlowPlugin from "./.opencode/plugins/delivery-flow.js";

        const hooks = await deliveryFlowPlugin({
          directory: path.resolve("docs"),
          worktree: path.resolve("."),
        });
        const output = {
          system: ["  preserve me  "],
        };

        await hooks["experimental.chat.system.transform"]({}, output);

        const bootstrapOnly = { system: [] };
        await hooks["experimental.chat.system.transform"]({}, bootstrapOnly);

        console.log(JSON.stringify({
          system: output.system,
          bootstrap: bootstrapOnly.system[0],
        }));
        """
    )

    system = payload["system"]
    bootstrap = payload["bootstrap"]

    assert system[0] == "  preserve me  "
    _assert_opencode_bootstrap(bootstrap)
    assert system[1] == bootstrap


def test_opencode_plugin_does_not_duplicate_bootstrap_when_any_text_part_has_it() -> None:
    payload = _run_node_json(
        """
        import path from "node:path";
        import deliveryFlowPlugin from "./.opencode/plugins/delivery-flow.js";

        const hooks = await deliveryFlowPlugin({
          directory: path.resolve("docs"),
          worktree: path.resolve("."),
        });
        const bootstrapOnly = { system: [] };
        await hooks["experimental.chat.system.transform"]({}, bootstrapOnly);

        const output = {
          system: [
            bootstrapOnly.system[0],
            "Existing system guidance.",
          ],
        };

        await hooks["experimental.chat.system.transform"]({}, output);

        console.log(JSON.stringify({
          system: output.system,
          bootstrap: bootstrapOnly.system[0],
        }));
        """
    )

    system = payload["system"]
    bootstrap = payload["bootstrap"]

    assert isinstance(system, list)
    assert len(system) == 2
    assert system[0] == bootstrap
    assert system[1] == "Existing system guidance."
    _assert_opencode_bootstrap(bootstrap)
