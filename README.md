# Delivery Flow

`delivery-flow` is a compact shared agent skill surface and controller contract
for keeping one task plan moving through
`spec -> plan -> task-by-task dev/review/fix -> finalize -> wait` without
handing the loop back to the owner after each stage.

[中文文档](./README.zh-CN.md) | [Architecture](./docs/architecture.md) | [Codex Guide](./docs/platforms/codex.md) | [Claude/Cursor Guide](./docs/platforms/claude.md) | [OpenCode Guide](./docs/platforms/opencode.md)

docs/ is human-facing. skills/ is agent-facing and contains the AI-facing skill entrypoints and supporting references.

Platform capability split:

- Codex installs the shared skill tree for discovery-only use and does not inject a session-start bootstrap
- Claude Code, Cursor, and OpenCode are bootstrap-capable and front-load the shared root routing contract before any response

Shared scope: the repository is not Codex-only. It publishes one shared skill
surface, with platform differences limited to discovery-only versus
bootstrap-capable startup behavior. Codex remains discovery-only and has no
session-start bootstrap parity. For platform shorthand, this remains the
Codex versus Claude/Cursor/OpenCode capability split.

## Status

- official skill entrypoints live under `skills/delivery-flow/` and `skills/using-delivery-flow/`
- Codex install path is `~/.agents/skills/delivery-flow`, and Codex is discovery-only today
- Claude Code and Cursor are bootstrap-capable and use `SessionStart` bootstrap via `.claude-plugin` and `.cursor-plugin`
- OpenCode is bootstrap-capable and auto-loads `.opencode/plugins/delivery-flow.js`
- default-use path enters the runtime directly
- post-plan execution stays task-by-task until a terminal stop
- repository verification baseline is `uv run pytest`, completes successfully, and all repository tests pass

## Highlights

- explicit mode selection: `superpowers-backed` or `fallback`
- explicit `execution_strategy` workflow state: `subagent-driven`, `inline`, or `unresolved`
- after planning, the main agent keeps execution moving until a terminal stop
- execution-strategy priority is `owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- in `superpowers-backed`, `subagent-driven` uses subagents and explicit `inline` stays valid in the current session; `fallback` preserves the same owner-facing loop natively
- if `execution_strategy=unresolved`, the main agent may ask once after planning; otherwise it must not reopen a generic execution-choice prompt
- the owner can explicitly change execution strategy mid-run, and the new strategy applies from the next schedulable task
- once `delivery-flow` owns post-plan workflow, upstream generic templates must not override a determined strategy
- `fix` is non-terminal, always re-enters `review`, and does not stop at task boundaries
- strict `pass`: unresolved required changes, testing issues, or maintainability issues keep the task open
- task-loop evidence: completed task, pending task, open issues, and owner acceptance state

## Platform Install

Human docs live under `docs/`. Agent-facing skill contracts and supporting references live under `skills/`.

### Codex

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

Manual install from the standard skill clone path:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/delivery-flow/skills ~/.agents/skills/delivery-flow
```

Shared skill surface:

```text
~/.agents/skills/delivery-flow/
├── delivery-flow/
│   └── SKILL.md
└── using-delivery-flow/
    └── SKILL.md
```

### Claude Code and Cursor

Install the plugin, restart the session, and let the platform run the
delivery-flow `SessionStart` bootstrap.

The bootstrap does not replace the skill contract. It only front-loads routing
so ongoing delivery threads can prefer `delivery-flow`.

Claude Code and Cursor are bootstrap-capable. They inject a strong root-routing bootstrap before any response, evaluate each new user turn, take ownership of an ongoing delivery thread when appropriate, and yield only when the request is truly single-phase.

### OpenCode

OpenCode installs the repository as a plugin and registers the shared `skills/`
directory automatically. No `AGENTS.md` is required.

OpenCode is also bootstrap-capable. Its plugin appends a strong root-routing bootstrap before any response so review/fix continuation stays inside `delivery-flow` while single-phase work still yields.

## Human Docs

- [README.zh-CN](./README.zh-CN.md)
  Chinese human overview.
- [docs/architecture.md](./docs/architecture.md)
  Human-facing architecture and call-flow guide.
- [docs/architecture.zh-CN.md](./docs/architecture.zh-CN.md)
  Chinese human-facing architecture and call-flow guide.
- [docs/platforms/codex.md](./docs/platforms/codex.md)
  Human-facing Codex install and usage guide.
- [docs/platforms/codex.zh-CN.md](./docs/platforms/codex.zh-CN.md)
  Chinese human-facing Codex install and usage guide.
- [docs/platforms/claude.md](./docs/platforms/claude.md)
  Human-facing Claude Code and Cursor install guide.
- [docs/platforms/claude.zh-CN.md](./docs/platforms/claude.zh-CN.md)
  Chinese human-facing Claude Code and Cursor install guide.
- [docs/platforms/opencode.md](./docs/platforms/opencode.md)
  Human-facing OpenCode install and usage guide.
- [docs/platforms/opencode.zh-CN.md](./docs/platforms/opencode.zh-CN.md)
  Chinese human-facing OpenCode install and usage guide.

## AI Skill Files

- [skills/delivery-flow/SKILL.md](./skills/delivery-flow/SKILL.md)
  AI-facing execution skill contract.
- [skills/delivery-flow/selection-contract.md](./skills/delivery-flow/selection-contract.md)
  Selection-time supporting contract for `delivery-flow`.
- [skills/delivery-flow/router-contract.md](./skills/delivery-flow/router-contract.md)
  Router-first supporting contract.
- [skills/delivery-flow/superpowers-backed.md](./skills/delivery-flow/superpowers-backed.md)
  `superpowers-backed` supporting backend contract.
- [skills/delivery-flow/fallback.md](./skills/delivery-flow/fallback.md)
  `fallback` supporting backend contract.
- [skills/delivery-flow/verification-scenarios.md](./skills/delivery-flow/verification-scenarios.md)
  Supporting verification scenarios for the execution skill.
- [skills/using-delivery-flow/SKILL.md](./skills/using-delivery-flow/SKILL.md)
  AI-facing root routing skill contract.
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  Agent-facing install instructions for Codex raw fetch flows.

## Repository Layout

- `skills/`
  Official shared skill entrypoints for installation and discovery.
- `src/delivery_flow/controller.py`
  Controller contract helpers and public runtime launcher.
- `src/delivery_flow/runtime/`
  Executable runtime, stop rules, and engine state progression.
- `src/delivery_flow/trace/`
  Run trace and terminal evidence holder.
- `src/delivery_flow/adapters/`
  Runtime-facing `superpowers-backed` and `fallback` adapters.
- `docs/platforms/`
  Human-facing installation guides for Codex, Claude Code, Cursor, and OpenCode.
- `docs/architecture.md`
  Human-facing architecture walkthrough for the markdown contract to runtime flow.
- `skills/delivery-flow/`
  Execution skill entrypoint plus supporting AI-facing contracts and verification references.
- `tests/`
  Repository verification baseline.

## Skill Selection Guide

`delivery-flow` should be treated as the top-level orchestrator for an ongoing delivery thread.

`delivery-flow` is router-first: on each new user turn, it should decide whether to take ownership of an ongoing delivery thread or yield when only a single phase is needed.

| Situation | Prefer |
| --- | --- |
| A new task needs requirement clarification or design exploration | `brainstorming` |
| A design is approved and the immediate next job is to write an implementation plan | `writing-plans` |
| A plan exists and the work can finish through linear execution | `executing-plans` |
| Even if a plan already exists, the work is still an ongoing delivery thread with likely review/fix continuation | `delivery-flow` |
| Owner keeps adding review findings and expects one main agent to continue the thread | `delivery-flow` |

Key rules:

- even if a plan already exists, prefer `delivery-flow` over `executing-plans` for an ongoing delivery thread
- review/fix continuation is a strong signal that `delivery-flow` should stay in control
- do not switch away merely because planning is complete
- take ownership when the new user turn continues an ongoing delivery thread
- yield when only a single phase is needed, such as brainstorming-only, plan-only, or one-shot work

## Common Mis-Selection Patterns

- Wrong: a plan already exists, so the top-level skill should switch to `executing-plans`
- Right: the plan exists, but the thread still needs continuous review/fix continuation, so `delivery-flow` remains the top-level orchestrator
- Wrong: brainstorming or planning finished, so the outer workflow should move to a different process skill
- Right: `brainstorming`, `writing-plans`, and `executing-plans` are stage-specific or subordinate workflows relative to `delivery-flow` when the same thread still needs continuous delivery ownership

## Verification

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

Expected result: `uv run pytest` completes successfully and all repository tests pass.

## Current Scope

This repository centers on one runtime-backed owner-facing workflow loop:

- the shared skill surface can be installed across supported platforms; Codex
  uses discovery-only wiring while Claude Code, Cursor, and OpenCode add
  bootstrap-capable startup routing
- the controller runtime executes `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
- post-plan execution keeps explicit `execution_strategy`: `subagent-driven`, `inline`, or `unresolved`
- execution-strategy priority is `owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- after planning, the main agent keeps execution moving until a terminal stop
- in `superpowers-backed`, `subagent-driven` runs post-plan `dev/review/fix` through subagents and explicit `inline` runs them in the current session; `fallback` preserves the same contract natively
- if `execution_strategy` is unresolved, the main agent may ask once after planning
- if `execution_strategy` is already determined, the skill must not reopen a generic execution-choice prompt
- if the owner explicitly changes execution strategy mid-run, the new strategy applies from the next schedulable task
- once `delivery-flow` owns post-plan workflow, upstream generic templates do not override the determined strategy
- the runtime advances one planned task at a time, and `fix` always returns to `review`
- task boundaries do not stop the loop; the next task starts immediately after strict task-level `pass`
- strict `pass` rejects unresolved required changes, testing issues, and maintainability issues
- early terminal stops such as `needs_owner_decision` or verification-unavailable return to the owner
- the default-use path enters the runtime directly
- the final result surfaces `completed_task_ids`, `pending_task_id`, `open_issue_summaries`, and `owner_acceptance_required`
- workflow tests cover pass, blocker recovery, repeated blocker, needs-owner-decision, and verification-unavailable paths
