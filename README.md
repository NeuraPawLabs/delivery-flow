# Delivery Flow

`delivery-flow` is the repository for the Delivery Flow skill and its supporting
controller artifacts.

Current repository state:

- root `SKILL.md` owner-facing skill entry
- controller skeleton
- explicit backend mode selection
- owner-visible mode banner
- `superpowers-backed` backend contract
- `fallback` backend contract
- dual-mode consistency scenarios

## Files

- `SKILL.md`
  Main skill entrypoint for Codex consumption.
- `superpowers-backed.md`
  Mapping from controller actions to `superpowers` capabilities.
- `fallback.md`
  Minimum parity contract when `superpowers` is unavailable.
- `verification-scenarios.md`
  Stop-rule and mode-consistency checks.

## Install As A Skill

For Codex, tell the agent:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

Local skill entrypoint:

```text
~/.codex/skills/delivery-flow/SKILL.md
```

Agent-facing install guide:

```text
.codex/INSTALL.md
```

Detailed Codex guide:

```text
docs/README.codex.md
```

Manual install for the current machine:

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/projects/delivery-flow ~/.codex/skills/delivery-flow
```

## Local Verification

```bash
cd /home/mm/workdir/projects/delivery-flow
uv run pytest
```

Current baseline: `11 passed`

Once installed, the skill exposes one controller contract with two execution
modes:

- `superpowers-backed`
- `fallback`
