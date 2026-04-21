# Delivery-Flow Platform Bootstrap Design

## Goal

Make `delivery-flow` behave more like a top-level workflow controller after installation, without relying on repository-local `AGENTS.md` prompts and without modifying third-party projects such as `superpowers`.

The target outcome is:

- installing the `delivery-flow` plugin/skill should be enough to activate its intended routing behavior
- supported platforms should prefer `delivery-flow` for ongoing delivery threads
- single-phase tasks should still yield cleanly to normal stage-specific skills

## Problem Statement

`delivery-flow` currently has a strong execution contract but a weak entry layer.

Its existing `SKILL.md` defines:

- router-first ownership for ongoing delivery threads
- precedence over `executing-plans` when review/fix continuation is likely
- explicit workflow ownership after planning

That contract only matters after the skill is selected. In practice, `superpowers` has a stronger first-move design because it combines:

- a broad root skill (`using-superpowers`)
- platform-specific bootstrap injection on platforms that support hooks
- native skill discovery integration on platforms that do not

`delivery-flow` needs the same kind of entry architecture rather than a larger single `SKILL.md`.

## Non-Goals

This design does not:

- modify `superpowers`
- depend on repository-level `AGENTS.md`
- replace the existing `delivery-flow` execution contract
- make one platform-specific plugin format the source of truth for every platform
- force `delivery-flow` to own brand-new brainstorming-only or plan-only threads

## Architecture

The repository should be split into three conceptual layers:

1. Core workflow skill
   - existing `delivery-flow` skill remains the source of truth for orchestration semantics
   - it owns execution strategy, task loop behavior, stop rules, and owner-facing delivery contract

2. Root routing skill
   - add a new `using-delivery-flow` skill
   - it owns selection-time routing only
   - its job is to decide whether the conversation should be handed to `delivery-flow`

3. Platform entry layer
   - add platform-specific plugin and bootstrap files
   - these files exist only to make `using-delivery-flow` reliably visible at session start

This keeps routing logic separate from execution logic and allows platform-specific bootstrap work without duplicating workflow semantics.

## Root Skill Design

### `using-delivery-flow` responsibility

`using-delivery-flow` should be intentionally thin.

Its job is to:

- inspect whether the current user turn belongs to an ongoing delivery thread
- route to `delivery-flow` when continuous ownership is required
- yield when the task is clearly a single-phase or one-shot task

It should not:

- define task execution stages
- duplicate execution strategy rules
- restate the full runtime contract
- become a second full workflow spec

### Selection signals

`using-delivery-flow` should prefer `delivery-flow` when one or more of these signals are present:

- the user is continuing a previously active implementation thread
- a spec or plan already exists and the thread still needs ongoing ownership
- review feedback has arrived and the same main agent should continue fix/review loops
- the user expectation is continuous end-to-end movement until `pass` or owner input is required

### Yield signals

`using-delivery-flow` should yield when the request is clearly:

- brainstorming-only
- plan-only
- a simple one-shot execution request
- a linear task with no ongoing ownership requirement

## Platform Strategy

The repository should support multiple AI coding platforms, but not by pretending they all expose the same plugin model.

### Claude Code and Cursor

Use plugin manifests plus `SessionStart` hooks.

At session start, inject a short bootstrap message that:

- announces `delivery-flow` routing support is installed
- requires checking whether `using-delivery-flow` should take the top-level routing role
- states that ongoing delivery threads should prefer `delivery-flow`
- states that single-phase tasks should yield to stage-specific skills

This bootstrap should be short and routing-focused. It should not inline the entire `delivery-flow` contract.

### OpenCode

Use OpenCode's plugin system to do two things:

- register the repository `skills/` directory
- inject the same short bootstrap context through the platform's system transform or equivalent plugin hook

The OpenCode behavior should mirror Claude/Cursor conceptually even if the mechanism differs.

### Codex

Use native skill discovery as the primary mechanism.

Codex support should not depend on `AGENTS.md`. Instead:

- install instructions should expose the repository `skills/` directory to Codex's skill discovery
- `using-delivery-flow` should be written broadly enough to act as a root routing skill in native discovery environments

If Codex later gains a stable plugin bootstrap mechanism worth targeting, it can be added as another platform entry layer, but the initial Codex path should optimize for the simplest robust install.

## Bootstrap Content

The bootstrap text should be minimal and stable across platforms.

Recommended content:

- `delivery-flow` provides top-level routing for ongoing delivery threads
- before responding, check whether `using-delivery-flow` should route the conversation
- if the thread needs continuous ownership, prefer `delivery-flow`
- if the task is single-phase, yield to the normal stage-specific skills

The bootstrap must not:

- embed the full `delivery-flow` spec
- redefine execution rules that already live in `delivery-flow`
- create platform-specific workflow semantics

## File Layout

The minimum implementation should introduce these files and directories:

- `skills/using-delivery-flow/SKILL.md`
- `hooks/session-start`
- `hooks/hooks.json`
- `hooks/hooks-cursor.json`
- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`
- platform installation docs for Codex / Claude Code / OpenCode

The existing root `SKILL.md` can remain as the `delivery-flow` execution skill, but the repository should move toward a dedicated `skills/` directory as the long-term shared skill surface.

## Installation Experience

The installation story should aim for "install once, routing works" with no extra prompt files.

Expected user experience by platform:

- Claude Code: install plugin, restart session, bootstrap runs automatically
- Cursor: install plugin, restart session, bootstrap runs automatically
- OpenCode: add plugin, restart session, bootstrap and skills registration happen automatically
- Codex: install the skill package into native skill discovery, restart session, `using-delivery-flow` becomes discoverable without extra `AGENTS.md`

## Testing Strategy

Verification should cover both static structure and behavioral intent.

### Static checks

- plugin manifests exist for Claude/Cursor
- hook config files point to the correct bootstrap script
- `using-delivery-flow` exists and has valid frontmatter
- platform install docs reference the right paths and expected restart behavior

### Contract checks

Add tests that verify:

- `using-delivery-flow` is described as a root routing skill
- it prefers `delivery-flow` for ongoing delivery threads
- it yields for single-phase tasks
- platform docs do not require `AGENTS.md`

### Manual smoke expectations

- installing on Claude/Cursor should surface the bootstrap before normal task work
- installing on Codex should make both root routing and execution skills discoverable
- continuing a delivery thread should prefer `delivery-flow` over `executing-plans`

## Risks and Mitigations

### Risk: bootstrap becomes too large

If the session-start message includes too much workflow detail, it will become brittle and expensive.

Mitigation:

- keep bootstrap limited to routing rules
- keep execution semantics inside `delivery-flow`

### Risk: Codex does not honor root routing strongly enough

Codex may still behave differently from hook-driven platforms because its initial integration relies on native skill discovery instead of a session hook.

Mitigation:

- write `using-delivery-flow` with an explicit, broad root-routing description
- keep Codex install docs focused on exposing the correct skill directory
- treat later Codex-specific bootstrap support as an additive enhancement

### Risk: duplicated semantics drift between files

If routing rules are restated differently in bootstrap text, `using-delivery-flow`, and `delivery-flow`, the system will become inconsistent.

Mitigation:

- define routing semantics in `using-delivery-flow`
- keep bootstrap text as a thin pointer to that routing skill
- keep execution semantics only in `delivery-flow`

## Recommendation

Implement the minimum viable platform bootstrap in this order:

1. add `using-delivery-flow` as the root routing skill
2. add Claude/Cursor plugin manifests and session-start bootstrap
3. add OpenCode plugin entry and docs
4. add Codex-native installation docs for the new `skills/` layout
5. add tests that lock the routing contract and installation assumptions

This sequence delivers the fastest path to "install the plugin and it behaves as intended" while keeping the workflow contract clean and platform-specific behavior isolated.
