---
name: delivery-flow
description: Use when one main agent should continuously drive requirement discussion, planning, development, review, and fix work until completion or owner input is required, preferring superpowers capabilities when available and falling back when they are not.
---

# Delivery Flow

## Overview

Delivery Flow is a workflow controller skill. It keeps one owner-facing contract stable across two execution modes:

- `superpowers-backed`
- `fallback`

The controller owns workflow semantics. Backends provide capability but do not redefine review results, stop rules, or final stop-and-wait behavior.

## When to Use

- Use when one main agent should keep `spec -> dev -> review -> fix -> stop` moving without the owner manually restarting each stage.
- Use when you want `superpowers` to act as a preferred capability backend instead of the workflow owner.
- Use when both `superpowers-backed` and `fallback` runs must preserve the same owner-visible contract.
- Do not use when the workflow needs persistent task-board synchronization or multi-project coordination.

## Mode Selection

Supported modes:

- `superpowers-backed`
- `fallback`

Mode selection must be explicit.

If required `superpowers` capabilities are available, select `superpowers-backed`.

If they are unavailable, select `fallback`.

Every run must explicitly declare the selected mode:

- `mode=superpowers-backed`
- `mode=fallback`

Silent fallback is forbidden.

## Controller Contract

Only the main agent may:

- decide the next workflow stage
- dispatch the next backend action
- interpret review results as workflow transitions
- declare completion
- return control to the owner

All review outcomes must be normalized into exactly one of:

- `pass`
- `blocker`
- `needs_owner_decision`

The controller must never consume backend-native review categories directly as workflow state.

The workflow is complete only when:

1. normalized review result is `pass`
2. the owner explicitly accepts the current state

## Driver Interface

Every backend must implement the same action surface:

- `discuss_and_spec`
- `plan`
- `run_dev`
- `run_review`
- `run_fix`
- `finalize`

Review normalization happens at the controller boundary.

## Stop Rules

The controller must stop when:

- normalized review result is `pass`
- normalized review result is `needs_owner_decision`
- required verification cannot be completed with available evidence
- the same blocker survives two consecutive fix-review cycles

After every terminal state, the controller must summarize delivery, summarize verification and residual risk, and explicitly say it is waiting for the owner's next instruction.

## Supporting Docs

- `superpowers-backed.md`
  Purpose: action mapping and mode contract for the preferred backend.
- `fallback.md`
  Purpose: parity contract for the native fallback backend.
- `verification-scenarios.md`
  Purpose: dual-mode consistency checks, especially stop-rule behavior.

## Quick Reference

- controller owns workflow semantics
- mode is always explicit
- review results normalize to `pass / blocker / needs_owner_decision`
- no explicit `pass` means no completion
- terminal states end in stop-and-wait
