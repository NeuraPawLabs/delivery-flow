---
name: implementation-review
description: Use when reviewing an implementation in any project for spec compliance, architecture fit, design pattern appropriateness, test quality, maintainability, security, performance, or delivery readiness.
---

# Implementation Review

## Overview

Use this skill to perform a strict implementation review. The review must decide whether the implementation is ready to ship, blocked by required changes, or blocked by an owner decision.

This is not for handling feedback from another reviewer. Use `receiving-code-review` for that.

## Review Workflow

1. Gather context: read the user request, active plan, linked spec, diff, relevant code, tests, docs, and local project instructions.
2. Find the active implementation plan before treating any spec as required scope.
3. Trace the plan to its associated spec. Treat specs without an associated plan as not yet in development, not as required implementation scope.
4. Build a requirement checklist from the active plan and its linked spec, then user request, README/API contracts, tests, and existing behavior.
5. Inspect the implementation against each requirement and against existing codebase patterns.
6. Inspect tests and verification evidence. Identify commands already run, commands that still need to run, and gaps that prevent confidence.
7. Classify the result as `pass`, `blocker`, or `needs_owner_decision`.
8. Report findings first, ordered by severity, with concrete file and line references when available.

## Evidence Requirements

- Do not claim pass without evidence from code inspection and required verification.
- Do not review against a spec directly until a plan links it to the current implementation.
- If multiple specs exist and no active plan identifies the implementation scope, return `needs_owner_decision`.
- If the spec is unavailable, say `spec unavailable` and build the checklist from the user request, docs, tests, and existing behavior.
- If required verification cannot be run, include it under `Commands not run` with the reason.
- Record `Commands run` and `Commands not run` explicitly in the final review.
- Treat unverified required behavior as residual risk or a blocker, depending on severity and available evidence.
- Do not infer acceptance from green tests alone; tests must correspond to the requirements.

## Review Dimensions

- Spec traceability: every required behavior is implemented; no unapproved scope creep hides risk.
- Behavior correctness: happy paths, edge cases, error paths, state transitions, API contracts, and backwards compatibility.
- Test quality: requirement-level tests, regression coverage, failure paths, meaningful assertions, and real verification commands.
- Architecture fit: module boundaries, dependency direction, existing helper/API reuse, layering, and integration with local patterns.
- Design pattern appropriateness: abstractions and patterns solve real complexity without premature generalization or unnecessary indirection.
- Maintainability: naming, cohesion, readability, localized change, duplication, comments, and long-term ownership cost.
- Security: authorization, secrets, injection, path handling, unsafe deserialization, sensitive logs, and dangerous operations.
- Performance: unnecessary I/O, N+1 behavior, unbounded loops or memory, hot-path work, caching, and scalability limits.
- Concurrency: race conditions, idempotency, locking, transactions, retries, partial failure recovery, and illegal states.
- Operational readiness: configuration, migrations, rollback, observability, deployment compatibility, and feature flags.
- UX / API ergonomics: user-visible errors, loading/error/empty states, accessibility, responsive behavior, and stable API responses.

## Result Model

- `pass`: No required changes remain, spec-relevant behavior is implemented, and verification evidence is sufficient.
- `blocker`: Required behavior is missing or wrong, tests are insufficient for required behavior, architecture/design creates material risk, or required verification is unavailable for a high-risk change.
- `needs_owner_decision`: The spec is ambiguous or conflicting, the implementation makes an unapproved product/architecture tradeoff, or multiple valid fixes require owner choice.

Strictness rules:

- `fix` or reviewer suggestions are not terminal; a changed implementation must be reviewed again.
- Style-only issues are not blockers unless they create maintainability or correctness risk.
- An approval with unresolved required changes is still `blocker`.
- If a finding depends on missing context, mark it as a question or residual risk instead of inventing certainty.

## Output Contract

Use this shape:

```text
Result: pass | blocker | needs_owner_decision

Findings:
- Severity: blocker | required_change | suggestion | question
- Location: path:line
- Requirement: spec/plan/request item or engineering principle
- Impact: user-visible, correctness, maintainability, security, performance, or operational effect
- Fix: concrete change needed
- Verification: command or inspection needed to confirm

Residual Risk:
- ...

Verification:
- Commands run:
- Commands not run:

Next Action:
- ...
```

When there are no findings, say so explicitly and still list residual risk and verification evidence.

Language rule for human-facing review output:

- Default to the user's current-turn language for human-facing review output.
- Keep contract field names such as `Result`, `Findings`, `Residual Risk`, `Verification`, and `Next Action` in English when the output shape requires them.
- Keep code identifiers, file paths, commands, error messages, API names, and handoff prompts in their original language.
- This language rule applies only to the human-facing review response, not internal classification, evidence gathering, or machine-readable contract markers.

Set `Next Action` by result:

- `pass`: say no follow-up `delivery-flow` run is needed.
- `blocker`: include a ready-to-run handoff prompt that starts with `Use delivery-flow to fix the implementation-review findings:` and lists the findings, active plan, linked spec, affected files, and required verification.
- `needs_owner_decision`: ask the exact owner question needed before any fix run starts.

## Common Mistakes

- Do not review only the diff if the behavior depends on surrounding code.
- Do not treat architectural preference as a blocker without showing concrete risk.
- Do not bury blockers after summaries.
- Do not omit tests from the review; missing tests can be the primary finding.
- Do not ask the owner to decide issues that the codebase or spec already resolves.
