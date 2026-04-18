# Delivery Flow

`delivery-flow` is a Codex skill and controller contract for keeping one task
plan moving through `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
without handing the loop back to the owner after each stage.

[中文文档](./README.zh-CN.md) | [Codex Guide](./docs/README.codex.md) | [Codex 中文指南](./docs/README.codex.zh-CN.md)

## Status

- skill entrypoint exists at `SKILL.md`
- local skill install path is `~/.codex/skills/delivery-flow`
- default-use path now enters the executable stage-2 runtime
- default-use path now runs a task-by-task runtime after planning
- real-task runtime validation has passed
- repository verification baseline is `uv run pytest` -> `80 passed`

## Highlights

- explicit mode selection: `superpowers-backed` or `fallback`
- controller-owned review normalization: `pass / blocker / needs_owner_decision`
- controller-owned blocker identity derivation
- task-loop evidence: completed tasks, pending task, open issues, and owner acceptance state
- includes the explicit `running_finalize` stage before `waiting_for_owner`
- task-level `pass` advances to the next task; only full-plan success reaches `finalize`
- runtime-owned trace and owner-visible stop-and-wait contract after terminal states

## Quick Install For Codex

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

Manual install for the current machine:

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/projects/delivery-flow ~/.codex/skills/delivery-flow
```

Local skill entrypoint:

```text
~/.codex/skills/delivery-flow/SKILL.md
```

## Documentation

- [README.zh-CN](./README.zh-CN.md)
  Chinese project overview.
- [docs/README.codex.md](./docs/README.codex.md)
  Codex installation and usage guide.
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  Chinese Codex installation and usage guide.
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  Agent-facing install instructions for Codex raw fetch flows.
- [SKILL.md](./SKILL.md)
  Skill contract loaded by Codex.
- [docs/stage-2-real-task-validation.md](./docs/stage-2-real-task-validation.md)
  Published runtime-backed validation evidence.

## Repository Layout

- `SKILL.md`
  Main skill entrypoint.
- `src/delivery_flow/controller.py`
  Controller contract helpers and public runtime launcher.
- `src/delivery_flow/runtime/`
  Executable stage-2 runtime, stop rules, and engine state progression.
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
cd /home/mm/workdir/projects/delivery-flow
uv run pytest
```

Current baseline: `80 passed`

## Current Scope

This repository now proves a runtime-backed owner-facing workflow loop:

- the skill can be installed and discovered by Codex
- the controller runtime executes `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
- the runtime advances one planned task at a time and only starts the next task after the current task passes review
- early terminal stops such as `needs_owner_decision` or verification-unavailable return without entering `running_finalize`
- the default-use path enters the runtime directly
- the final result surfaces `completed_task_ids`, `pending_task_id`, `open_issue_summaries`, and `owner_acceptance_required`
- on full-plan success, `owner_acceptance_required` is determined by the finalization result and may be `True` or `False`
- workflow tests cover pass, blocker recovery, repeated blocker, needs-owner-decision, and verification-unavailable paths
- one runtime-backed validation run has been published as repository evidence
- reviewer re-review has confirmed the runtime-backed continuous loop behavior

## Next Steps

Future work is no longer “finish the first release”. It is a new round of goals,
for example:

- larger end-to-end task validation
- broader real-task validation
- workflow evidence publication
- broader backend parity hardening
