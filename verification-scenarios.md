# Verification Scenarios

Use these scenarios to check that the skill still shapes behavior correctly.

## Scenario 1: Discovery Works

- install the skill through `~/.codex/skills/delivery-flow`
- expect `SKILL.md` to exist at the linked path
- expect Codex to discover the skill on a fresh session start

## Scenario 2: Activation Works

- start one session that names `delivery-flow` explicitly
- start one session whose task clearly matches the `SKILL.md` description
- expect the skill to be selected in both cases

## Scenario 3: Compliance Contract Holds

- once the skill is active, expect the main agent to own workflow transitions after planning
- expect the main agent to keep execution moving continuously until a terminal stop
- expect post-plan execution to be task-by-task
- expect review results to normalize to `pass / blocker / needs_owner_decision`
- expect no backend-native review wording to become workflow state

## Scenario 4: Planned Tasks Advance One At A Time

- run in `superpowers-backed`
- run in `fallback`
- expect task 2 to start only after task 1 reaches strict `pass`
- expect no stop/wait between passing task boundaries
- expect `finalize` only after all planned tasks reach `pass`
- expect explicit stop-and-wait after run-level `pass`

## Scenario 5: Superpowers-Backed Uses Subagents Post-Plan

- run in `superpowers-backed`
- expect post-plan `dev`, `review`, and `fix` to execute through subagents
- expect the main agent to keep scheduling rather than yielding after each subagent result

## Scenario 6: Needs Owner Decision Stops The Loop

- run in both modes
- expect normalized `needs_owner_decision`
- expect the current task to remain open
- expect no `finalize` when the runtime stops early for owner input
- expect control to return explicitly to the owner

## Scenario 7: Same Blocker Escalates After Two Fix-Review Cycles

- run in both modes
- expect blocker identity to be controller-owned
- expect stop after the second unresolved cycle
- expect normalized result to surface as owner-needed rather than infinite looping

## Scenario 8: Strict Pass Rejects Small Issue Accumulation

- run in both modes
- review returns `approved` plus unresolved required changes, testing issues, or maintainability issues
- expect normalization to downgrade to `blocker`
- expect the loop to continue through `fix -> review` rather than closing the task

## Scenario 9: Verification Unavailable Stops Honestly

- run in both modes
- review indicates changes are still required
- required verification cannot be completed with available evidence
- expect no guessed blocker identity
- expect no `finalize` on that path
- expect the summary to explain the verification gap

## Scenario 10: Fallback Preserves Parity

- compare `superpowers-backed` and `fallback`
- expect the same owner-facing task-loop contract in both modes
- expect fallback to preserve stop rules rather than silently weakening them

## Scenario 11: Mode Is Explicit

- run in both modes
- expect visible `mode=superpowers-backed` or `mode=fallback`
- expect no silent fallback

## Scenario 12: One Continuous Controller-Owned Run

- invoke `delivery-flow`
- expect one continuous controller-owned task loop after planning
- expect no owner restitching after non-terminal `review` / `fix`
- expect no owner restitching between passing tasks
- expect the final summary to say the runtime is waiting for the owner's next instruction
