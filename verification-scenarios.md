# Verification Scenarios

## Scenario 1: Pass Leads To Stop-And-Wait

- run in `superpowers-backed`
- run in `fallback`
- expect explicit stop-and-wait after normalized `pass`

## Scenario 2: Needs Owner Decision Stops

- run in both modes
- expect normalized `needs_owner_decision`
- expect stop and return to owner

## Scenario 3: Same Blocker Stops After Two Cycles

- run in both modes
- expect same-blocker identity to be controller-owned
- expect stop after the second unresolved cycle

## Scenario 4: Verification-Unavailable Stops Without Guessing Blocker Identity

- run in both modes
- review returns `changes_requested`
- one or more blocker identity fields are missing
- runtime stops with `required_verification_cannot_be_completed_with_available_evidence`
- terminal summary explains the evidence insufficiency reason

## Scenario 5: Mode Banner Is Explicit

- run in both modes
- expect visible `mode=superpowers-backed` or `mode=fallback`

## Scenario 6: Default Runtime Path

- invoke the public launcher / default-use path
- expect one continuous runtime-owned stage sequence
- expect the owner-visible final summary to include `waiting for the owner's next instruction`
