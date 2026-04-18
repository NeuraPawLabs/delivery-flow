# Fallback Mode

Use this mode only when the required `superpowers` capabilities are unavailable.

Fallback exists to preserve the same owner-facing workflow contract with a weaker capability backend.

## Expected Execution Shape

- `discuss_and_spec` is performed natively
- `plan` is performed natively
- `dev`, `review`, and `fix` still exist after planning
- `finalize` still runs only after all planned tasks reach `pass`

## Required Parity

Fallback may differ internally, but it must preserve:

- explicit mode reporting
- task-by-task post-plan execution
- normalized review results
- repeated-blocker escalation
- verification-unavailable escalation
- terminal stop-and-wait behavior

Fallback is not allowed to silently weaken the owner-facing contract just because the backend is weaker.
