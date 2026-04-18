# Superpowers-Backed Mode

Use this mode when the required `superpowers` capabilities are available.

## Expected Execution Shape

- `discuss_and_spec` uses the `superpowers` requirement/spec flow
- `plan` uses the planning flow already defined by `superpowers`
- after planning, the main agent dispatches subagents for:
  - `dev`
  - `review`
  - `fix`
- `finalize` runs once after all planned tasks reach `pass`

## Non-Negotiable Contract

This mode may reuse `superpowers` skills and subagents, but it may not redefine:

- explicit mode reporting
- task-by-task post-plan execution
- normalized review results
- repeated-blocker escalation
- verification-unavailable escalation
- terminal stop-and-wait behavior

Backend-native reviewer wording is only input. The controller must normalize it into:

- `pass`
- `blocker`
- `needs_owner_decision`
