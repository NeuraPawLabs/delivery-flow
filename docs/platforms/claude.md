# Delivery Flow for Claude Code and Cursor

[English](./claude.md) | [简体中文](./claude.zh-CN.md)

Guide for using `delivery-flow` with Claude Code and Cursor through the
repository plugin manifests and `SessionStart` bootstrap hooks.

## Quick Start

1. Open this repository in Claude Code or Cursor.
2. Install this repository as the plugin package so the root-relative
   `.claude-plugin`, `.cursor-plugin`, `hooks/`, and `skills/` paths stay
   intact.
3. Restart the session so `SessionStart` runs again.

## What Gets Installed

- the repository root is the install surface for Claude Code and Cursor
- `.claude-plugin/plugin.json` exposes the Claude Code plugin metadata
- `.cursor-plugin/plugin.json` exposes the Cursor plugin metadata
- `hooks/hooks.json` wires Claude Code `SessionStart`
- `hooks/hooks-cursor.json` wires Cursor `sessionStart`
- `hooks/session-start` emits a routing-focused bootstrap that points at `using-delivery-flow`
- `skills/` stays available at the install root for shared skill discovery

## Bootstrap Contract

- the bootstrap is `SessionStart` only
- it does not replace the `delivery-flow` skill contract
- it front-loads routing so ongoing delivery threads can prefer `delivery-flow`
- single-phase work should still yield to the normal skill ecosystem

## Bootstrap Strength

Claude Code and Cursor are bootstrap-capable platforms.

At session start, the plugin injects a strong root-routing bootstrap for the
shared `delivery-flow` contract. This root-routing bootstrap runs before any
response. On each new user turn, the agent is instructed to decide whether to
take ownership of an ongoing delivery thread, route into `delivery-flow` when
it does, and yield only when the request is truly single-phase.

The strong contract also states that plan presence alone is not enough to yield
and that review/fix continuation is a strong signal for keeping the thread
inside `delivery-flow`.

## Verify

Check the plugin manifests:

```bash
test -f .claude-plugin/plugin.json
test -f .cursor-plugin/plugin.json
```

Check the hook wiring:

```bash
grep -n "SessionStart\\|sessionStart\\|using-delivery-flow" hooks/hooks.json hooks/hooks-cursor.json hooks/session-start
```

Run the focused contract slice:

```bash
uv run pytest tests/test_platform_bootstrap.py -q
```

Start a fresh session and confirm the startup routing mentions
`using-delivery-flow` before normal task work.

## Notes

- the bootstrap is routing-only
- the runtime contract still lives in `delivery-flow`
- no `AGENTS.md` file is required
