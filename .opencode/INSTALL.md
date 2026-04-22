# Delivery Flow for OpenCode

Enable the repository-local OpenCode plugin and routing bootstrap.

## Prerequisites

- OpenCode
- Node.js

## What Gets Installed

- `package.json` exposes the plugin entry at `.opencode/plugins/delivery-flow.js`
- the plugin registers the repository worktree `skills/` directory through the OpenCode `config` hook
- the plugin appends a routing-only bootstrap through `experimental.chat.system.transform`
- the bootstrap points OpenCode at `using-delivery-flow`

## Usage

1. Open this repository in OpenCode.
2. Let OpenCode auto-load the project-local plugin from `.opencode/plugins/`.
3. Start a new session in the repository.

The plugin keeps startup context narrow:

- it registers `skills/` so OpenCode can discover the repository skills
- it injects a routing-only bootstrap
- it references `using-delivery-flow` as the root routing skill
- it does not inline downstream execution behavior

## Verify

1. Confirm `package.json` points at `.opencode/plugins/delivery-flow.js`.
2. Confirm `.opencode/plugins/delivery-flow.js` defines `config(config)` and `experimental.chat.system.transform`.
3. Confirm the shared skills exist under `skills/using-delivery-flow/SKILL.md` and `skills/delivery-flow/SKILL.md`.
4. Start a new OpenCode session in this repository and ask: `What do the using-delivery-flow and delivery-flow skills do in this project?`

Expected result:

- OpenCode can describe both `using-delivery-flow` and `delivery-flow`
- the answer reflects routing-only bootstrap behavior for `using-delivery-flow`
- the answer does not require `AGENTS.md`

## Docs

- `docs/platforms/opencode.md`
- `docs/platforms/opencode.zh-CN.md`
