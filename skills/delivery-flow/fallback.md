# Fallback Mode

Use this mode only when the required `superpowers` capabilities are unavailable.

Fallback exists to preserve the same owner-facing workflow contract with a weaker capability backend.

## Expected Execution Shape

- `discuss_and_spec` is performed natively
- `plan` is performed natively
- after planning, the main agent keeps execution moving continuously until a terminal stop
- execution strategy remains controller-owned workflow state after planning
- `dev`, `review`, and `fix` still exist after planning and are executed natively
- non-terminal `review` never stops at a task boundary: it either advances to the next task or enters `fix`
- `fix` is non-terminal and must always be followed by `review`
- `finalize` still runs only after all planned tasks reach strict `pass`

## Execution Strategy Rules

- if `execution_strategy=unresolved`, the main agent may ask once after planning before starting post-plan work
- if execution strategy is already determined, `fallback` must not re-open that choice through generic upstream templates
- fallback preserves the same strategy semantics even when executor capability is weaker than `superpowers-backed`
- if the owner explicitly changes strategy mid-run, the controller applies the change from the next schedulable task

## Required Parity

Fallback may differ internally, but it must preserve:

- explicit mode reporting
- task-by-task post-plan execution
- continuous controller-owned execution after planning
- normalized review results
- strict pass requirements
- repeated-blocker escalation
- verification-unavailable escalation
- no stop/wait at task boundaries or after non-terminal `review` / `fix`
- terminal stop-and-wait behavior

Fallback is not allowed to silently weaken the owner-facing contract just because the backend is weaker.

Fallback must normalize backend-native reviewer wording into exactly:

- `pass`
- `blocker`
- `needs_owner_decision`
