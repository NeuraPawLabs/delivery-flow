# Superpowers-Backed Mode

Use this mode when the required `superpowers` capabilities are available.

## Expected Execution Shape

- `discuss_and_spec` uses the `superpowers` requirement/spec flow
- `plan` uses the planning flow already defined by `superpowers`
- after planning, the main agent keeps execution moving continuously until a terminal stop
- execution strategy remains controller-owned workflow state after planning
- if `execution_strategy=subagent-driven`, post-plan `dev`, `review`, and `fix` are executed via subagents
- if `execution_strategy=inline`, the main agent executes post-plan `dev`, `review`, and `fix` in the current session while preserving the same controller-owned loop
- non-terminal `review` never stops at a task boundary: it either advances to the next task or enters `fix`
- `fix` is non-terminal and must always be followed by `review`
- `finalize` runs once after all planned tasks reach strict `pass`

## Execution Strategy Rules

- if `execution_strategy=unresolved`, the main agent may ask once after planning before dispatching post-plan work
- if execution strategy is already determined, `superpowers-backed` must not re-open that choice through generic upstream templates
- if no stronger preset exists, `superpowers-backed` defaults determined post-plan strategy to `subagent-driven`
- `inline` remains a valid explicit strategy in this mode when chosen by the owner or a stronger preset
- if the owner explicitly changes strategy mid-run, the controller applies the change from the next schedulable task rather than silently continuing with the old one

## Non-Negotiable Contract

This mode may reuse `superpowers` skills and subagents, but it may not redefine:

- explicit mode reporting
- task-by-task post-plan execution
- continuous controller-owned execution after planning
- normalized review results
- strict pass requirements
- repeated-blocker escalation
- verification-unavailable escalation
- no stop/wait at task boundaries or after non-terminal `review` / `fix`
- terminal stop-and-wait behavior

Backend-native reviewer wording is only input. The controller must normalize it into:

- `pass`
- `blocker`
- `needs_owner_decision`
