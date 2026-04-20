# Delivery-Flow Selection Contract

[简体中文](./selection-contract.zh-CN.md)

This document defines the selection-time contract for `delivery-flow`.

## Top-Level Role

- `delivery-flow` is the top-level orchestrator for an ongoing delivery thread.
- The thread still belongs to `delivery-flow` when one main agent must keep work moving until a terminal stop.
- This remains true even if the thread already has a written spec, an approved plan, or active implementation work in progress.

## Precedence Rules

- Even if a plan already exists, `delivery-flow` remains the preferred top-level skill for an ongoing delivery thread.
- Existing plan presence alone is not enough to prefer `executing-plans`.
- Prefer `delivery-flow` over `executing-plans` when the thread includes or is likely to include review/fix continuation.
- Do not switch away merely because planning is complete.

## Relationship To Other Process Skills

- `brainstorming` is for shaping requirements and designs, not for owning long-running delivery orchestration.
- `writing-plans` is for producing an implementation plan, not for owning post-plan delivery orchestration.
- `executing-plans` is for stable, linear execution that can finish without ongoing delivery ownership.
- `brainstorming`, `writing-plans`, and `executing-plans` are stage-specific or subordinate workflows relative to `delivery-flow` when both apply.

## Selection Guide

| Situation | Preferred Top-Level Skill |
| --- | --- |
| A new feature needs requirement clarification or design exploration | `brainstorming` |
| A design is approved and the next job is to write an implementation plan | `writing-plans` |
| A written plan exists and the work can finish through linear execution | `executing-plans` |
| A written plan exists but the thread is an ongoing delivery thread | `delivery-flow` |
| Review feedback keeps arriving and one main agent must continue implementation, review, and fix loops | `delivery-flow` |

## Correctness Checks

- If the owner keeps supplying feedback and expects the same main agent to continue, treat that as an ongoing delivery thread.
- If review/fix continuation is likely, keep `delivery-flow` as the top-level orchestrator.
- If a plan exists but continuous delivery ownership is still required, `delivery-flow` still wins the selection decision.
