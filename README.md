# Delivery Flow

`delivery-flow` is a Codex skill and controller contract for keeping one task
moving through `spec -> dev -> review -> fix -> stop` without handing the loop
back to the owner after each stage.

[中文文档](./README.zh-CN.md) | [Codex Guide](./docs/README.codex.md) | [Codex 中文指南](./docs/README.codex.zh-CN.md)

## Status

- skill entrypoint exists at `SKILL.md`
- local skill install path is `~/.codex/skills/delivery-flow`
- real-task E2E validation has passed
- repository verification baseline is `uv run pytest` -> `11 passed`

## Highlights

- explicit mode selection: `superpowers-backed` or `fallback`
- controller-owned review normalization: `pass / blocker / needs_owner_decision`
- controller-owned blocker identity derivation
- owner-visible stop-and-wait contract after terminal states

## Quick Install For Codex

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

Manual install for the current machine:

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/projects/delivery-flow ~/.codex/skills/delivery-flow
```

Local skill entrypoint:

```text
~/.codex/skills/delivery-flow/SKILL.md
```

## Documentation

- [README.zh-CN](./README.zh-CN.md)
  Chinese project overview.
- [docs/README.codex.md](./docs/README.codex.md)
  Codex installation and usage guide.
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  Chinese Codex installation and usage guide.
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  Agent-facing install instructions for Codex raw fetch flows.
- [SKILL.md](./SKILL.md)
  Skill contract loaded by Codex.

## Repository Layout

- `SKILL.md`
  Main skill entrypoint.
- `src/delivery_flow/controller.py`
  Controller contract helpers, mode selection, review normalization, blocker identity.
- `src/delivery_flow/drivers/superpowers.py`
  Preferred backend adapter surface.
- `superpowers-backed.md`
  Preferred backend contract.
- `fallback.md`
  Fallback backend contract.
- `verification-scenarios.md`
  Dual-mode consistency scenarios.
- `tests/`
  Repository verification baseline.

## Verification

```bash
cd /home/mm/workdir/projects/delivery-flow
uv run pytest
```

Current baseline: `11 passed`

## Current Scope

This repository now proves one real owner-facing workflow loop:

- the skill can be installed and discovered by Codex
- the controller contract is documented
- one real task has demonstrated `spec -> plan -> dev -> review -> fix`
- reviewer re-review has confirmed the owner-facing continuous loop behavior

## Next Steps

Future work is no longer “finish the first release”. It is a new round of goals,
for example:

- larger end-to-end task validation
- repeated blocker cycles
- `needs_owner_decision` terminal-state validation
- broader backend parity hardening
