# Delivery Flow for Codex

Enable `delivery-flow` as a local Codex skill.

## Quick Install

```bash
git clone git@github.com:NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
mkdir -p ~/.codex/skills
ln -s ~/.codex/delivery-flow ~/.codex/skills/delivery-flow
```

Then restart Codex.

## Prerequisites

- Git
- OpenAI Codex CLI

## Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
   ```

2. **Create the local skill link:**
   ```bash
   mkdir -p ~/.codex/skills
   ln -s ~/.codex/delivery-flow ~/.codex/skills/delivery-flow
   ```

   If the link already exists:
   ```bash
   rm ~/.codex/skills/delivery-flow
   ln -s ~/.codex/delivery-flow ~/.codex/skills/delivery-flow
   ```

3. **Restart Codex** so skill discovery reloads.

## Verify

Check the skill entrypoint:

```bash
test -L ~/.codex/skills/delivery-flow
readlink -f ~/.codex/skills/delivery-flow
test -f ~/.codex/skills/delivery-flow/SKILL.md
```

Run the repo verification baseline:

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

Expected result:

- the symlink resolves to the repo
- `SKILL.md` exists at the linked path
- `uv run pytest` reports `11 passed`

## Updating

```bash
cd ~/.codex/delivery-flow
git pull
uv run pytest
```

The skill link keeps pointing at the updated repo.

For a fuller guide, see `docs/README.codex.md` in the repository.

## Uninstalling

```bash
rm ~/.codex/skills/delivery-flow
```

Optionally remove the clone:

```bash
rm -rf ~/.codex/delivery-flow
```
