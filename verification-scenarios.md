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
- expect execution strategy to be controller-owned workflow state rather than ad hoc conversation memory
- expect execution strategy resolution priority to stay `owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`

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

## Scenario 6: Execution Strategy Unresolved Asks Once

- strategy is still unresolved after planning
- multiple valid post-plan execution paths remain
- expect one post-plan execution-strategy question
- expect no repeated execution-choice question after the strategy becomes determined

## Scenario 7: Determined Strategy Does Not Reopen

- strategy is already determined before or at planning completion
- expect post-plan execution to begin without reopening `1/2` or equivalent generic execution-choice prompts
- expect generic upstream planning templates not to override the determined strategy
- expect `superpowers-backed` to honor explicit `inline` as well as `subagent-driven`

## Scenario 8: Owner Changes Strategy Mid-Run

- strategy is already determined
- owner explicitly changes it during the active run
- expect the controller to update workflow state
- expect the new strategy to apply from the next schedulable task

## Scenario 8A: Existing Plan But Ongoing Delivery Thread

- thread already has a written plan
- owner continues asking for review/fix/further implementation
- expect `delivery-flow` to remain the top-level workflow controller

## Scenario 8B: Review Feedback Arrives Mid-Execution

- a run is already active
- owner supplies new review findings
- expect the workflow to stay inside `delivery-flow`

## Scenario 8C: Plan Presence Alone Does Not Select executing-plans

- both `delivery-flow` and `executing-plans` appear superficially applicable
- continuous delivery ownership is still required
- expect delivery-flow precedence

## Scenario 8D: Brainstorming Completes But Delivery Flow Owns The Thread

- brainstorming finished
- delivery is not finished
- expect `delivery-flow` to own post-plan orchestration

## Scenario 9: Needs Owner Decision Stops The Loop

- run in both modes
- expect normalized `needs_owner_decision`
- expect the current task to remain open
- expect no `finalize` when the runtime stops early for owner input
- expect control to return explicitly to the owner

## Scenario 10: Same Blocker Escalates After Two Fix-Review Cycles

- run in both modes
- expect blocker identity to be controller-owned
- expect stop after the second unresolved cycle
- expect the runtime to stop in an owner-facing terminal state rather than infinite looping

## Scenario 11: Strict Pass Rejects Small Issue Accumulation

- run in both modes
- review returns `approved` plus unresolved required changes, testing issues, or maintainability issues
- expect normalization to downgrade to `blocker`
- expect the loop to continue through `fix -> review` rather than closing the task

## Scenario 12: Verification Unavailable Stops Honestly

- run in both modes
- review indicates changes are still required
- required verification cannot be completed with available evidence
- expect no guessed blocker identity
- expect no `finalize` on that path
- expect the summary to explain the verification gap

## Scenario 13: Fallback Preserves Parity

- compare `superpowers-backed` and `fallback`
- expect the same owner-facing task-loop contract in both modes
- expect fallback to preserve stop rules rather than silently weakening them

## Scenario 14: Mode Is Explicit

- run in both modes
- expect visible `mode=superpowers-backed` or `mode=fallback`
- expect no silent fallback

## Scenario 15: One Continuous Controller-Owned Run

- invoke `delivery-flow`
- expect one continuous controller-owned task loop after planning
- expect no owner restitching after non-terminal `review` / `fix`
- expect no owner restitching between passing tasks
- expect the final summary to say the runtime is waiting for the owner's next instruction
