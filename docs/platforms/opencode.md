# Delivery Flow for OpenCode

[English](./opencode.md) | [简体中文](./opencode.zh-CN.md)

Guide for using `delivery-flow` with OpenCode through the repository-local
plugin entry.

## Quick Start

1. Open this repository in OpenCode.
2. Let OpenCode auto-load `.opencode/plugins/delivery-flow.js` from `.opencode/plugins/`.
3. Start a new session in the repository.

## What the Plugin Does

- registers the repository worktree `skills/` directory through the OpenCode `config hook`
- adds a routing-only bootstrap through `experimental.chat.system.transform`
- points startup routing at `using-delivery-flow`
- keeps bootstrap scope limited to route selection instead of downstream execution details

## Bootstrap Strength

OpenCode is a bootstrap-capable platform.

The plugin appends a strong root-routing bootstrap for the shared
`delivery-flow` contract to `output.system`, so the agent receives the same
"before any response" routing rule as Claude Code and Cursor. On each new user
turn, that root-routing bootstrap tells the agent to decide whether to take
ownership of an ongoing delivery thread before normal task work begins.

That bootstrap states that review/fix continuation is a strong signal for
staying inside `delivery-flow`, while single-phase work should yield to the
normal skill ecosystem.

## Files

- `package.json`
- `.opencode/plugins/delivery-flow.js`
- `.opencode/INSTALL.md`

## Verify

Check the package entry:

```bash
node -e "console.log(JSON.parse(require('node:fs').readFileSync('package.json', 'utf8')).main)"
```

Check the plugin source:

```bash
grep -n "config(config)\\|experimental.chat.system.transform\\|using-delivery-flow\\|routing-only" .opencode/plugins/delivery-flow.js
```

On Windows PowerShell:

```powershell
Select-String -Path .opencode/plugins/delivery-flow.js -Pattern "config\\(config\\)|experimental\\.chat\\.system\\.transform|using-delivery-flow|routing-only"
```

Check the shared skill files:

```bash
test -f skills/using-delivery-flow/SKILL.md
test -f skills/delivery-flow/SKILL.md
```

On Windows PowerShell:

```powershell
Test-Path skills/using-delivery-flow/SKILL.md
Test-Path skills/delivery-flow/SKILL.md
```

Run the focused test slice:

```bash
uv run pytest tests/test_platform_bootstrap.py -q
```

Do one real OpenCode smoke check in a fresh session:

```text
What do the using-delivery-flow and delivery-flow skills do in this project?
```

Expected result: OpenCode can describe both skills from the repo-local
`skills/` directory, with `using-delivery-flow` framed as routing-only bootstrap.

## Behavior Contract

- `using-delivery-flow` is the root routing skill
- startup bootstrap stays routing-only
- the plugin should not inline downstream workflow semantics

See `../../.opencode/INSTALL.md` for the install summary.
