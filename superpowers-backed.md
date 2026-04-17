# Superpowers-Backed Mode

## Action Mapping

- `discuss_and_spec` -> `brainstorming`
- `plan` -> `writing-plans`
- `run_dev` -> `subagent-driven-development` implementer phase
- `run_review` -> `subagent-driven-development` review phases and `requesting-code-review` when needed
- `run_fix` -> `subagent-driven-development` implementer rework phase
- `finalize` -> controller-owned closeout after backend execution completes

## Mode Contract

This backend may reuse `superpowers` capability blocks, but it may not redefine:

- mode visibility
- review normalization
- stop rules
- stop-and-wait completion behavior

Backend-native review output must be normalized by the controller into:

- `pass`
- `blocker`
- `needs_owner_decision`
