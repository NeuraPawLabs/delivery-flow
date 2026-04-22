---
name: delivery-flow
description: Use when `delivery-flow` should act as the router-first top-level process skill for an ongoing delivery thread; on each new user turn, take ownership even if a plan already exists or review feedback has arrived, and yield when only a single phase is needed, while `brainstorming`, `writing-plans`, `receiving-code-review`, `executing-plans`, and `test-driven-development` stay stage-specific or subordinate and one main agent keeps the same thread moving through task-by-task dev/review/fix until pass or owner input is required.
---

# Delivery Flow

`delivery-flow` is router-first: before it enters execution, it decides whether the current user turn belongs to an ongoing delivery thread.

Use this skill when one main agent should keep work moving through:

- `spec`
- `plan`
- task-by-task `dev -> review -> fix -> review ...`
- `finalize`
- `wait`

The main agent owns workflow control. Backends provide capability, but they do not define workflow state.

## Routing Decision

Re-evaluate routing on each new user turn.

If the user turn belongs to an ongoing delivery thread, `delivery-flow` should take ownership as the top-level orchestrator.

If only a single phase is needed, `delivery-flow` should yield to the normal skill ecosystem instead of over-capturing the thread.

Do not re-route on every internal phase boundary once `delivery-flow` already owns the thread.

## When To Take Ownership

- a plan already exists and the same thread must continue
- review feedback has arrived and the same thread must continue through fix/review continuation
- the owner is continuing an existing delivery thread on a new user turn
- one main agent must keep the same thread moving until `pass` or owner input is required

## When To Yield

- the request is only requirement clarification or brainstorming for a brand-new task
- the request is only to write a plan for a single phase
- the request is a one-shot task that does not require ongoing delivery ownership
- only a single phase is needed, so `delivery-flow` should yield rather than take ownership

## Use It When

- one main agent should keep the workflow moving without the owner restarting every stage
- planned work should execute task by task rather than as one coarse dev/review pass
- `superpowers-backed` and `fallback` runs must preserve the same owner-facing contract

## Selection Priority

- `delivery-flow` is the top-level orchestrator for an ongoing delivery thread
- even if a plan already exists, `delivery-flow` remains the preferred top-level skill for an ongoing delivery thread
- existing plan presence alone is not enough to prefer `executing-plans`
- prefer `delivery-flow` over `executing-plans` when the thread includes or is likely to include review/fix continuation
- review/fix continuation should keep `delivery-flow` in control
- do not switch away from `delivery-flow` merely because planning is complete

Do not use it for:

- multi-project coordination
- external task-board synchronization
- workflows that need a different owner-facing contract per backend

## Relationship To Other Process Skills

- `brainstorming` is for requirement clarification and design shaping, not long-running delivery orchestration
- `writing-plans` is for producing an implementation plan, not owning post-plan delivery orchestration
- `executing-plans` is for stable linear execution that can finish without ongoing delivery ownership
- `brainstorming`, `writing-plans`, and `executing-plans` are stage-specific or subordinate workflows relative to `delivery-flow` when both apply

## Core Contract

- mode is explicit:
  - `mode=superpowers-backed`
  - `mode=fallback`
- execution strategy is explicit workflow state:
  - `execution_strategy=subagent-driven`
  - `execution_strategy=inline`
  - `execution_strategy=unresolved`
- after ownership is taken, execution stays task-by-task `dev -> review -> fix -> review ...` until strict `pass`
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

## Execution Strategy

`delivery-flow` owns execution strategy once it owns post-plan workflow.

Execution strategy resolves by this priority:

1. the current owner's explicit instruction
2. already-determined workflow state inside the active `delivery-flow` run
3. project or repository-local preset if one exists
4. `delivery-flow` default strategy
5. upstream generic skill or template behavior

Question timing is strict:

- if `execution_strategy=unresolved` and multiple valid post-plan paths remain, the main agent may ask once after planning
- if execution strategy is already determined, the main agent must not ask again at task boundaries, review loops, or later plan handoffs
- if the owner explicitly changes strategy mid-run, the main agent updates workflow state and applies it from the next schedulable task

Override rule:

- once `delivery-flow` has taken ownership of post-plan workflow, upstream generic planning templates must not reopen execution-strategy selection if strategy is already determined

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
- main agent owns `execution_strategy`
- unresolved strategy may trigger one post-plan question
- determined strategy must not trigger repeated execution-choice prompts
- main agent keeps post-plan execution moving until a terminal stop
- subagents execute post-plan work in `superpowers-backed`
- fallback keeps the same owner-facing loop without `superpowers`
- controller owns workflow semantics
- no backend-native review category becomes workflow state
- no explicit `pass` means no task closure
- terminal states end in stop-and-wait
