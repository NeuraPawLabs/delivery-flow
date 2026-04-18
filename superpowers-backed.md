# Superpowers-Backed Mode

## Action Mapping

- `discuss_and_spec` -> `brainstorming`
- `plan` -> `writing-plans`
- `run_dev` -> implement the current planned task with `subagent-driven-development`
- `run_review` -> review the current planned task result with `subagent-driven-development` review phases and `requesting-code-review` when needed
- `run_fix` -> rework the current planned task after a blocker review result
- `finalize` -> run once after all planned tasks pass successfully

## Mode Contract

This backend may reuse `superpowers` capability blocks, but it may not redefine:

- mode visibility
- review normalization
- stop rules
- stop-and-wait completion behavior
- task-by-task execution after planning
- no backend-owned `finalize` call on early terminal stops
- `owner_acceptance_required` reporting in `RuntimeResult` and the final summary

Backend-native review output must be normalized by the controller into:

- `pass`
- `blocker`
- `needs_owner_decision`
