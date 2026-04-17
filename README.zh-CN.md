# Delivery Flow

[English](README.md) | [简体中文](README.zh-CN.md)

`delivery-flow` 是一个面向 Codex 的工作流 skill 仓库，用来把同一条任务持续推进到：

- `spec`
- `dev`
- `review`
- `fix`
- `stop`

它保持一套稳定的 owner-facing contract，并支持两种显式 mode：

- `superpowers-backed`
- `fallback`

## 当前状态

当前仓库已经完成首轮实现，并具备可消费的 skill 入口：

- skill 入口：`~/.codex/skills/delivery-flow/SKILL.md`
- 远端仓库：`git@github.com:NeuraPawLabs/delivery-flow.git`
- 当前验证基线：`uv run pytest` -> `11 passed`

## 安装

### 给 Codex 的快捷安装入口

告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

### 详细安装文档

- Codex 安装指南：`docs/README.codex.md`
- Codex 安装指南（中文）：`docs/README.codex.zh-CN.md`
- agent-facing 安装入口：`.codex/INSTALL.md`

### 当前机器上的本地安装方式

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/projects/delivery-flow ~/.codex/skills/delivery-flow
```

## 使用场景

适用于这些场景：

- 你希望主 agent 持续驱动 `spec -> dev -> review -> fix`
- 你不希望流程在每一轮 review 后重新断回 owner 手里
- 你希望 `superpowers-backed` 和 `fallback` 保持同一套 owner-visible contract

不适用于这些场景：

- 需要跨多个项目做持久化任务编排
- 需要独立的 task board / coordinator 基础设施

## 仓库内容

- `SKILL.md`
  主 skill 入口。
- `.codex/INSTALL.md`
  给 Codex/agent 直接消费的安装说明。
- `docs/README.codex.md`
  给人类阅读的英文 Codex 安装说明。
- `docs/README.codex.zh-CN.md`
  给人类阅读的中文 Codex 安装说明。
- `superpowers-backed.md`
  `superpowers` 后端动作映射与 mode contract。
- `fallback.md`
  `fallback` 后端最小一致性 contract。
- `verification-scenarios.md`
  双 mode 一致性与 stop-rule 验证场景。

## 本地验证

```bash
cd /home/mm/workdir/projects/delivery-flow
uv run pytest
```

当前基线：`11 passed`

## 更新与卸载

更新仓库：

```bash
cd ~/.codex/delivery-flow && git pull
uv run pytest
```

卸载 skill：

```bash
rm ~/.codex/skills/delivery-flow
rm -rf ~/.codex/delivery-flow
```
