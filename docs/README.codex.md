# Delivery Flow for Codex

[English](README.codex.md) | [简体中文](README.codex.zh-CN.md)

Guide for installing and using `delivery-flow` with Codex via native skill
discovery.

## Quick Install

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

## Manual Installation

### Prerequisites

- OpenAI Codex
- Git
- `uv` for local verification

### Steps

1. Clone the repo:
   ```bash
   git clone git@github.com:NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
   ```

2. Create the skill symlink:
   ```bash
   mkdir -p ~/.codex/skills
   ln -s ~/.codex/delivery-flow ~/.codex/skills/delivery-flow
   ```

3. Restart Codex.

### Windows

Use a junction instead of a symlink:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills"
cmd /c mklink /J "$env:USERPROFILE\.codex\skills\delivery-flow" "$env:USERPROFILE\.codex\delivery-flow"
```

## How It Works

Codex scans `~/.codex/skills/` at session start, reads `SKILL.md` frontmatter,
and loads skills on demand. `delivery-flow` becomes visible through this
symlink:

```text
~/.codex/skills/delivery-flow -> ~/.codex/delivery-flow
```

Once installed, the skill exposes one controller contract with two explicit
modes:

- `superpowers-backed`
- `fallback`

## Usage

Start a new Codex session and ask for a task that should benefit from
continuous delivery orchestration, for example:

- "Use delivery-flow to keep this feature moving through spec, dev, review, and fix."
- "Run this task with delivery-flow and stop only when owner input is required."

Codex should discover the skill automatically when:

- you mention `delivery-flow` by name
- the task matches the `SKILL.md` description

## Verify Installation

Verify the skill entry:

```bash
test -L ~/.codex/skills/delivery-flow
readlink -f ~/.codex/skills/delivery-flow
test -f ~/.codex/skills/delivery-flow/SKILL.md
```

Verify the repository baseline:

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

Expected baseline: `27 passed`

## Default Runtime Path

Once installed, `delivery-flow` defaults into one runtime-backed controller loop:

- explicit `superpowers-backed` / `fallback` mode selection
- runtime-owned `spec -> plan -> dev -> review -> fix -> stop`
- run trace evidence and owner-visible terminal summary
- no owner restitching between stages

## Updating

```bash
cd ~/.codex/delivery-flow && git pull
uv run pytest
```

Restart Codex after updating so the next session picks up the latest skill
metadata.

## Uninstalling

```bash
rm ~/.codex/skills/delivery-flow
rm -rf ~/.codex/delivery-flow
```

## Troubleshooting

### Skill not showing up

1. Verify the symlink: `ls -la ~/.codex/skills/delivery-flow`
2. Check the skill entry exists: `test -f ~/.codex/skills/delivery-flow/SKILL.md`
3. Restart Codex. Skill discovery happens at session start.

### Tests do not run

1. Make sure `uv` is installed.
2. Run `uv sync` inside `~/.codex/delivery-flow` if the environment is missing.
3. Re-run `uv run pytest`.
