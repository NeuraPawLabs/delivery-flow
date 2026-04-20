# Delivery Flow

`delivery-flow` is a compact Codex skill and controller contract for keeping one task
plan moving through `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
without handing the loop back to the owner after each stage.

[中文文档](./README.zh-CN.md) | [Codex Guide](./docs/README.codex.md) | [Codex 中文指南](./docs/README.codex.zh-CN.md)

## Status

- skill entrypoint exists at `SKILL.md`
- local skill install path is `~/.codex/skills/delivery-flow`
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

## Quick Install For Codex

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

Manual install for the current machine:

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/code/python/delivery-flow ~/.codex/skills/delivery-flow
```

Local skill entrypoint:

```text
~/.codex/skills/delivery-flow/SKILL.md
```

## Documentation

- [README.zh-CN](./README.zh-CN.md)
  Chinese overview.
- [selection-contract.md](./selection-contract.md)
  Selection-time contract and precedence rules.
- [router-contract.md](./router-contract.md)
  Router-first take-ownership and yield rules.
- [docs/README.codex.md](./docs/README.codex.md)
  Codex install and usage guide.
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  Chinese Codex install and usage guide.
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  Agent-facing install instructions for Codex raw fetch flows.
- [SKILL.md](./SKILL.md)
  Skill contract loaded by Codex.

## Repository Layout

- `SKILL.md`
  Main skill entrypoint.
- `src/delivery_flow/controller.py`
  Controller contract helpers and public runtime launcher.
- `src/delivery_flow/runtime/`
  Executable runtime, stop rules, and engine state progression.
- `src/delivery_flow/trace/`
  Run trace and terminal evidence holder.
- `src/delivery_flow/adapters/`
  Runtime-facing `superpowers-backed` and `fallback` adapters.
- `superpowers-backed.md`
  Preferred backend contract.
- `fallback.md`
  Fallback backend contract.
- `verification-scenarios.md`
  Dual-mode consistency scenarios.
- `selection-contract.md`
  Selection boundary and precedence contract.
- `router-contract.md`
  Router-first take-ownership and yield contract.
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

## Observability Service

- all projects now write to one global observability database
- the default database path resolves to `DELIVERY_FLOW_HOME/observability/observability.db`
- passing `project_root` must not fork data into a project-local observability database
- the read side stays independent: runtime writes do not depend on the backend service being up
- the backend exposes a read-only observability API and serves packaged frontend assets
- the React UI lives in `frontend/observability-ui`
- during development, run the frontend dev server separately from the Python backend service

Typical local workflow:

```bash
cd /home/mm/workdir/code/python/delivery-flow/frontend/observability-ui
npm install
npm run dev
```

Start the backend in a second shell:

```bash
cd /home/mm/workdir/code/python/delivery-flow
uv run delivery-flow-observability --host 127.0.0.1 --port 8000
```

Module form is also supported:

```bash
cd /home/mm/workdir/code/python/delivery-flow
uv run python -m delivery_flow.observability.cli --host 127.0.0.1 --port 8000
```

The frontend and backend remain separate in development. Vite proxies `/api` to `http://127.0.0.1:8000`.

To serve the built UI from the backend:

```bash
cd /home/mm/workdir/code/python/delivery-flow/frontend/observability-ui
npm install
npm run build

cd /home/mm/workdir/code/python/delivery-flow
python scripts/build_observability_ui.py frontend/observability-ui/dist
uv run delivery-flow-observability --host 127.0.0.1 --port 8000
```

In that packaged-static flow, the Python backend serves the built UI from package resources.

## Verification

```bash
cd /home/mm/workdir/code/python/delivery-flow
uv run pytest
```

Expected result: `uv run pytest` completes successfully and all repository tests pass.

## Current Scope

This repository centers on one runtime-backed owner-facing workflow loop:

- the skill can be installed and discovered by Codex
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
