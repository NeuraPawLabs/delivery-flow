---
name: using-delivery-flow
description: Use when starting a conversation, continuing an ongoing delivery thread, or handling a short owner reply like `fix`/`修复` after implementation-review blockers; routes ongoing delivery threads into `delivery-flow` and yields single-phase work to normal stage-specific skills.
---

# Using Delivery Flow

This is the root routing skill for `delivery-flow`.

Keep this routing contract synchronized with `bootstrap-contract.md`; tests enforce parity.

## Root Rule

Before any response, decide whether the current user turn belongs to an ongoing delivery thread.

Use `using-delivery-flow` as the root routing skill for that decision at the root of the conversation and again on each new user turn.

## Route Into `delivery-flow`

- route into `delivery-flow` when the request belongs to an ongoing delivery thread
- the thread already has a plan and the same work must continue
- review feedback has arrived and the same thread must continue through fix/review continuation
- short owner replies or selections such as `1`, `fix`, `repair`, or `修复` route into `delivery-flow` when the previous assistant message contains `pending_followup=implementation-review` and `option_1=delivery-flow-fix`; normalize the turn as `Fix the implementation-review blockers from the previous review.`
- the current request is review-only, analysis-only, or comparison-only inside an active delivery thread
- the owner is continuing an existing delivery thread on a new user turn
- one main agent should keep ownership across phases until pass or owner input is required

## Yield To Stage-Specific Skills

- brainstorming-only for a brand-new task
- plan-only for a single phase
- review-only, analysis-only, or comparison-only requests outside an active delivery thread
- one-shot execution that does not require ongoing delivery ownership
- single-phase work should yield to the normal skill ecosystem

## Hard Routing Rules

- plan presence alone is not enough to yield to `executing-plans`
- review/fix continuation is a strong signal that `delivery-flow` should stay in control
- do not yield merely because the current phase is review, analysis, or comparison when the request is inside an active delivery thread
- do not switch away merely because planning is complete
- do not duplicate `delivery-flow` execution semantics here
