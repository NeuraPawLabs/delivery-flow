---
name: delivery-flow
description: Use when one main agent should continuously drive requirement discussion, planning, and task-by-task dev/review/fix until pass or owner input is required, preferring superpowers capabilities when available and falling back when they are not.
---

# Delivery Flow

Use this skill when one main agent should keep work moving through:

- `spec`
- `plan`
- task-by-task `dev -> review -> fix -> review ...`
- `finalize`
- `wait`

The main agent owns workflow control. Backends provide capability, but they do not define workflow state.

## Use It When

- one main agent should keep the workflow moving without the owner restarting every stage
- planned work should execute task by task rather than as one coarse dev/review pass
- `superpowers-backed` and `fallback` runs must preserve the same owner-facing contract

Do not use it for:

- multi-project coordination
- external task-board synchronization
- workflows that need a different owner-facing contract per backend

## Core Contract

- mode is explicit:
  - `mode=superpowers-backed`
  - `mode=fallback`
- after planning, the main agent keeps execution moving task by task until a terminal stop
- post-plan execution is task-by-task
- in `superpowers-backed`, post-plan `dev`, `review`, and `fix` run via subagents
- in `fallback`, the same post-plan contract is preserved natively
- review results normalize to exactly:
  - `pass`
  - `blocker`
  - `needs_owner_decision`
- `fix` is never terminal by itself
- `fix` must always be followed by `review`
- no stop/wait at task boundaries or after non-terminal `review` / `fix`
- task-level `pass` advances to the next task
- run-level `pass` happens only after all planned tasks pass and `finalize` runs
- `pass` stays strict: unresolved required changes, testing issues, or maintainability issues are blockers
- terminal states always return control to the owner and wait

## Stop Rules

Stop autonomous execution when:

- review normalizes to `needs_owner_decision`
- required verification cannot be completed with available evidence
- the same blocker survives two consecutive `fix -> review` cycles
- all planned tasks have passed and `finalize` returns the closeout result

## Mode Selection

If required `superpowers` capabilities are available, use `superpowers-backed`.

If they are unavailable, use `fallback`.

Silent fallback is forbidden.

## Supporting Docs

- `superpowers-backed.md`
- `fallback.md`
- `verification-scenarios.md`

## Quick Reference

- main agent schedules
- main agent keeps post-plan execution moving until a terminal stop
- subagents execute post-plan work in `superpowers-backed`
- fallback keeps the same owner-facing loop without `superpowers`
- controller owns workflow semantics
- no backend-native review category becomes workflow state
- no explicit `pass` means no task closure
- terminal states end in stop-and-wait
