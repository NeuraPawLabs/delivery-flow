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
- after planning, the main agent keeps execution moving until a terminal stop
- `superpowers-backed` runs post-plan `dev/review/fix` through subagents; `fallback` preserves the same owner-facing loop natively
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
- `tests/`
  Repository verification baseline.

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
- after planning, the main agent keeps execution moving until a terminal stop
- in `superpowers-backed`, post-plan `dev/review/fix` run through subagents; `fallback` preserves the same contract natively
- the runtime advances one planned task at a time, and `fix` always returns to `review`
- task boundaries do not stop the loop; the next task starts immediately after strict task-level `pass`
- strict `pass` rejects unresolved required changes, testing issues, and maintainability issues
- early terminal stops such as `needs_owner_decision` or verification-unavailable return to the owner
- the default-use path enters the runtime directly
- the final result surfaces `completed_task_ids`, `pending_task_id`, `open_issue_summaries`, and `owner_acceptance_required`
- workflow tests cover pass, blocker recovery, repeated blocker, needs-owner-decision, and verification-unavailable paths
