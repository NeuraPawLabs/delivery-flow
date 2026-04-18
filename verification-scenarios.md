# Verification Scenarios

## Scenario 1: Planned Tasks Advance One At A Time And Then Stop-And-Wait

- run in `superpowers-backed`
- run in `fallback`
- expect task 2 to start only after task 1 passes review
- expect `running_finalize` before `waiting_for_owner` on full pass
- expect explicit stop-and-wait after normalized `pass`

## Scenario 2: Needs Owner Decision Stops

- run in both modes
- expect normalized `needs_owner_decision`
- expect completed-task and pending-task evidence for the current task loop state
- expect final summary to surface `owner acceptance required: yes` when owner input is still required
- expect no `running_finalize` when the runtime stops early for `needs_owner_decision`
- expect stop and return to owner

## Scenario 3: Same Blocker Stops After Two Cycles

- run in both modes
- expect same-blocker identity to be controller-owned
- expect stop after the second unresolved cycle

## Scenario 4: Verification-Unavailable Stops Without Guessing Blocker Identity

- run in both modes
- review returns `changes_requested`
- one or more blocker identity fields are missing
- expect no `running_finalize` when verification is unavailable mid-task
- runtime stops with `required_verification_cannot_be_completed_with_available_evidence`
- terminal summary explains the evidence insufficiency reason

## Scenario 5: Mode Banner Is Explicit

- run in both modes
- expect visible `mode=superpowers-backed` or `mode=fallback`

## Scenario 6: Default Runtime Path

- invoke the public launcher / default-use path
- expect one continuous runtime-owned task-loop stage sequence after planning
- expect no owner restitching between planned tasks
- expect the owner-visible final summary to include `waiting for the owner's next instruction`
