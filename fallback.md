# Fallback Mode

## Action Mapping

- `discuss_and_spec` -> native requirement discussion and spec drafting
- `plan` -> native plan drafting
- `run_dev` -> implement the current planned task natively
- `run_review` -> review the current planned task result natively
- `run_fix` -> rework the current planned task natively after a blocker review result
- `finalize` -> run once after all planned tasks pass successfully and emit the same owner-facing closeout contract

## Mode Contract

Fallback exists only to preserve minimum viable parity when `superpowers` is unavailable.

It must preserve the same owner-facing workflow semantics:

- explicit mode banner
- task-by-task execution after planning
- normalized review outputs
- verification-unavailable stop rule
- same-blocker two-cycle stop rule
- no fallback-owned `finalize` call on early terminal stops
- `owner_acceptance_required` in `RuntimeResult` and the final summary
- final stop-and-wait behavior
