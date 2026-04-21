# Delivery Flow for Codex

Enable `delivery-flow` as a local Codex skill through native skill discovery.

## Quick Install

```bash
git clone https://github.com/NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
mkdir -p ~/.agents/skills
ln -s ~/.codex/delivery-flow/skills ~/.agents/skills/delivery-flow
```

Then restart Codex.

## Prerequisites

- Git
- OpenAI Codex CLI
- `uv` for local verification

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
   ```

2. **Expose the shared skills directory:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/delivery-flow/skills ~/.agents/skills/delivery-flow
   ```

   If the link already exists:
   ```bash
   rm ~/.agents/skills/delivery-flow
   ln -s ~/.codex/delivery-flow/skills ~/.agents/skills/delivery-flow
   ```

3. **Restart Codex** so native skill discovery reloads.

### Windows

Use a junction instead of a symlink:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\delivery-flow" "$env:USERPROFILE\.codex\delivery-flow\skills"
```

The shared directory should look like this:

```text
~/.agents/skills/delivery-flow/
├── delivery-flow/
│   └── SKILL.md
└── using-delivery-flow/
    └── SKILL.md
```

This install path exposes both `skills/delivery-flow` and
`skills/using-delivery-flow` without requiring `AGENTS.md`.

## Verify

Check the shared skill directory:

```bash
test -L ~/.agents/skills/delivery-flow
ls -l ~/.agents/skills/delivery-flow
test -f ~/.agents/skills/delivery-flow/delivery-flow/SKILL.md
test -f ~/.agents/skills/delivery-flow/using-delivery-flow/SKILL.md
```

On Windows PowerShell:

```powershell
Get-Item "$env:USERPROFILE\.agents\skills\delivery-flow"
Test-Path "$env:USERPROFILE\.agents\skills\delivery-flow\delivery-flow\SKILL.md"
Test-Path "$env:USERPROFILE\.agents\skills\delivery-flow\using-delivery-flow\SKILL.md"
```

Run the repo verification baseline:

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

Expected result:

- the symlink resolves to the repo `skills/` directory
- `delivery-flow/SKILL.md` exists at the linked path
- `using-delivery-flow/SKILL.md` exists at the linked path
- `uv run pytest` completes successfully
- all repository tests pass

## Updating

```bash
cd ~/.codex/delivery-flow
git pull
uv run pytest
```

The `~/.agents/skills/delivery-flow` link keeps pointing at the updated repo
skills directory.

For a fuller guide, see `docs/README.codex.md` in the repository.

## Uninstalling

```bash
rm ~/.agents/skills/delivery-flow
```

On Windows PowerShell:

```powershell
Remove-Item "$env:USERPROFILE\.agents\skills\delivery-flow" -Force
```

Optionally remove the clone:

```bash
rm -rf ~/.codex/delivery-flow
```
