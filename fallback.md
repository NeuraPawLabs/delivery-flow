# Fallback Mode

Use this mode only when the required `superpowers` capabilities are unavailable.

Fallback exists to preserve the same owner-facing workflow contract with a weaker capability backend.

## Expected Execution Shape

- `discuss_and_spec` is performed natively
- `plan` is performed natively
- after planning, the main agent keeps execution moving continuously until a terminal stop
- `dev`, `review`, and `fix` still exist after planning and are executed natively
- non-terminal `review` never stops at a task boundary: it either advances to the next task or enters `fix`
- `fix` is non-terminal and must always be followed by `review`
- `finalize` still runs only after all planned tasks reach strict `pass`

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
