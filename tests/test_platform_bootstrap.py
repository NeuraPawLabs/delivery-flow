from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


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


def _assert_routing_bootstrap(bootstrap: str) -> None:
    assert "using-delivery-flow" in bootstrap
    assert "ongoing delivery threads" in bootstrap
    assert "routing-focused bootstrap" not in bootstrap
    assert "executing-plans" not in bootstrap
    assert "test-driven-development" not in bootstrap
    assert "brainstorming" not in bootstrap


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
