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

## Scenario 4: Verification Unavailable Stops

- run in both modes
- expect stop when required verification cannot be completed with available evidence

## Scenario 5: Mode Banner Is Explicit

- run in both modes
- expect visible `mode=superpowers-backed` or `mode=fallback`
