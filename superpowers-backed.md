# Superpowers-Backed Mode

Use this mode when the required `superpowers` capabilities are available.

## Expected Execution Shape

- `discuss_and_spec` uses the `superpowers` requirement/spec flow
- `plan` uses the planning flow already defined by `superpowers`
- after planning, the main agent keeps execution moving continuously until a terminal stop
- post-plan `dev`, `review`, and `fix` are executed via subagents
- non-terminal `review` never stops at a task boundary: it either advances to the next task or enters `fix`
- `fix` is non-terminal and must always be followed by `review`
- `finalize` runs once after all planned tasks reach strict `pass`

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
