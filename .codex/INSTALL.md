# Delivery Flow for Codex

Enable `delivery-flow` as a local Codex skill through native skill discovery.

## Quick Install

```bash
git clone https://github.com/NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
mkdir -p ~/.agents/skills
ln -s ~/.codex/delivery-flow/skills/delivery-flow ~/.agents/skills/delivery-flow
ln -s ~/.codex/delivery-flow/skills/using-delivery-flow ~/.agents/skills/using-delivery-flow
ln -s ~/.codex/delivery-flow/skills/implementation-review ~/.agents/skills/implementation-review
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

2. **Expose each shared skill directory:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/delivery-flow/skills/delivery-flow ~/.agents/skills/delivery-flow
   ln -s ~/.codex/delivery-flow/skills/using-delivery-flow ~/.agents/skills/using-delivery-flow
   ln -s ~/.codex/delivery-flow/skills/implementation-review ~/.agents/skills/implementation-review
   ```

   If old links already exist:
   ```bash
   rm ~/.agents/skills/delivery-flow
   rm -f ~/.agents/skills/using-delivery-flow ~/.agents/skills/implementation-review
   ln -s ~/.codex/delivery-flow/skills/delivery-flow ~/.agents/skills/delivery-flow
   ln -s ~/.codex/delivery-flow/skills/using-delivery-flow ~/.agents/skills/using-delivery-flow
   ln -s ~/.codex/delivery-flow/skills/implementation-review ~/.agents/skills/implementation-review
   ```

3. **Restart Codex** so native skill discovery reloads.

### Windows

Use a junction instead of a symlink:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\delivery-flow" "$env:USERPROFILE\.codex\delivery-flow\skills\delivery-flow"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\using-delivery-flow" "$env:USERPROFILE\.codex\delivery-flow\skills\using-delivery-flow"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\implementation-review" "$env:USERPROFILE\.codex\delivery-flow\skills\implementation-review"
```

The shared skill entries should look like this:

```text
~/.agents/skills/
├── delivery-flow/
│   └── SKILL.md
├── implementation-review/
│   └── SKILL.md
└── using-delivery-flow/
    └── SKILL.md
```

Each Codex skill must be exposed as its own direct child of
`~/.agents/skills`. Do not symlink the repository `skills/` directory as
`~/.agents/skills/delivery-flow`, because that makes the three skills appear as
nested content under one entry and can confuse skill selector display.

Codex may display these entries with a source namespace, such as
`delivery-flow:delivery-flow`, `delivery-flow:using-delivery-flow`, and
`delivery-flow:implementation-review`. That display shape is acceptable as long
as all three skills are discoverable.

## Capability Model

This install enables `delivery-flow` in discovery-only mode for Codex.

It exposes the shared skill tree through native skill discovery, but it does
not inject a session-start bootstrap and does not provide bootstrap parity with
Claude Code, Cursor, or OpenCode.

## Verify

Check the shared skill directory:

```bash
test -L ~/.agents/skills/delivery-flow
test -L ~/.agents/skills/using-delivery-flow
test -L ~/.agents/skills/implementation-review
test -f ~/.agents/skills/delivery-flow/SKILL.md
test -f ~/.agents/skills/using-delivery-flow/SKILL.md
test -f ~/.agents/skills/implementation-review/SKILL.md
codex debug prompt-input "list delivery-flow skills" | rg "delivery-flow:(delivery-flow|using-delivery-flow|implementation-review)"
```

On Windows PowerShell:

```powershell
Get-Item "$env:USERPROFILE\.agents\skills\delivery-flow"
Get-Item "$env:USERPROFILE\.agents\skills\using-delivery-flow"
Get-Item "$env:USERPROFILE\.agents\skills\implementation-review"
Test-Path "$env:USERPROFILE\.agents\skills\delivery-flow\SKILL.md"
Test-Path "$env:USERPROFILE\.agents\skills\using-delivery-flow\SKILL.md"
Test-Path "$env:USERPROFILE\.agents\skills\implementation-review\SKILL.md"
```

Run the repo verification baseline:

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

Expected result:

- each symlink resolves to its matching repo `skills/<skill-name>/` directory
- `delivery-flow/SKILL.md` exists as a direct skill entry
- `using-delivery-flow/SKILL.md` exists as a direct skill entry
- `implementation-review/SKILL.md` exists as a direct skill entry
- `codex debug prompt-input "list delivery-flow skills"` shows
  `delivery-flow:delivery-flow`, `delivery-flow:using-delivery-flow`, and
  `delivery-flow:implementation-review`
- the `/skills` UI may display them as namespaced entries
- `uv run pytest` completes successfully
- all repository tests pass

## Updating

```bash
cd ~/.codex/delivery-flow
git pull
uv run pytest
```

The `~/.agents/skills/<skill-name>` links keep pointing at the updated repo
skill directories.

For a fuller guide, see `docs/platforms/codex.md` in the repository.

Platform guides live under `docs/platforms/`. docs/ is human-facing.
Human-readable docs stay in `docs/`. skills/ is agent-facing. AI-facing skill
entrypoints and supporting references live under `skills/`.

Codex is discovery-only. This install exposes native skill discovery but does
not inject a session-start bootstrap, so there is no session-start bootstrap
parity here.

Bootstrap-capable platforms include Claude Code, Cursor, and OpenCode. Those
platforms can inject a strong root-routing bootstrap at session start, while
this Codex path only publishes the shared skills for discovery.

## Uninstalling

```bash
rm ~/.agents/skills/delivery-flow
rm ~/.agents/skills/using-delivery-flow
rm ~/.agents/skills/implementation-review
```

On Windows PowerShell:

```powershell
Remove-Item "$env:USERPROFILE\.agents\skills\delivery-flow" -Force
Remove-Item "$env:USERPROFILE\.agents\skills\using-delivery-flow" -Force
Remove-Item "$env:USERPROFILE\.agents\skills\implementation-review" -Force
```

Optionally remove the clone:

```bash
rm -rf ~/.codex/delivery-flow
```
