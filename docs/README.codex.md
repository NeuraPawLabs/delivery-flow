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
- post-plan execution strategy is explicit workflow state: `subagent-driven`, `inline`, or `unresolved`
- execution-strategy priority is `owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- after `plan`, the main agent keeps execution moving until a terminal stop
- in `superpowers-backed`, `subagent-driven` runs post-plan `dev/review/fix` via subagents and explicit `inline` keeps them in the current session
- `fix` must be followed by `review`, with no stop/wait at task boundaries
- strict `pass` rejects unresolved required changes, testing issues, and maintainability issues

## When delivery-flow should win over executing-plans

- `delivery-flow` is router-first on each new user turn
- `delivery-flow` is the top-level orchestrator for an ongoing delivery thread
- even if a plan already exists, prefer `delivery-flow` over `executing-plans` when one main agent must keep the thread moving
- review/fix continuation is the clearest signal that the thread still belongs to `delivery-flow`
- do not switch away merely because planning is complete
- yield when only a single phase is needed instead of over-capturing brainstorming-only, plan-only, or one-shot tasks

## Why plan existence alone is not enough

- a written plan does not remove the need for continuous delivery ownership
- if owner feedback is still arriving and the thread will continue through implementation, review, and fix, the selection should stay with `delivery-flow`
- `executing-plans` fits stable linear execution, not an ongoing delivery thread

## How delivery-flow relates to brainstorming and writing-plans

- `brainstorming` is for requirement clarification and design shaping
- `writing-plans` is for producing an implementation plan
- `brainstorming`, `writing-plans`, and `executing-plans` are stage-specific or subordinate workflows relative to `delivery-flow` when both apply

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

Expected result: `uv run pytest` completes successfully and all repository tests pass.

## Default Runtime Path

Once installed, `delivery-flow` defaults into one runtime-backed controller loop:

- explicit `superpowers-backed` / `fallback` mode selection
- explicit execution strategy state for post-plan execution: `subagent-driven`, `inline`, or `unresolved`
- execution-strategy priority is `owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- runtime-owned `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
- continuous main-agent execution after planning until a terminal stop
- in `superpowers-backed`, `subagent-driven` dispatches subagents for post-plan `dev/review/fix` and explicit `inline` keeps them in the current session
- if execution strategy is unresolved, the main agent may ask once after planning
- if execution strategy is already determined, the skill continues without reopening a generic execution-choice prompt
- if the owner explicitly changes execution strategy mid-run, the new strategy applies from the next schedulable task
- once `delivery-flow` owns post-plan workflow, upstream generic templates do not override the determined strategy
- non-terminal `review` either advances to the next task or enters `fix`; `fix` always returns to `review`
- strict `pass` rejects unresolved required changes, testing issues, and maintainability issues
- run trace evidence and owner-visible terminal summary
- no owner restitching between passing tasks

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
