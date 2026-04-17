# Fallback Mode

## Action Mapping

- `discuss_and_spec` -> native requirement discussion and spec drafting
- `plan` -> native plan drafting
- `run_dev` -> native development subagent dispatch
- `run_review` -> native review subagent dispatch
- `run_fix` -> native fix subagent dispatch
- `finalize` -> controller-owned closeout

## Mode Contract

Fallback exists only to preserve minimum viable parity when `superpowers` is unavailable.

It must preserve the same owner-facing workflow semantics:

- explicit mode banner
- normalized review outputs
- verification-unavailable stop rule
- same-blocker two-cycle stop rule
- final stop-and-wait behavior
