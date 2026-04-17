# Delivery Flow for Codex

这是给 Codex agent 看的中文安装与使用说明。

[English Version](./README.codex.md) | [项目主页](../README.zh-CN.md)

## 快速安装

直接告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

## 手动安装

### 前置条件

- OpenAI Codex
- Git
- `uv`，用于本地验证

### 步骤

1. 克隆仓库：
   ```bash
   git clone git@github.com:NeuraPawLabs/delivery-flow.git ~/.codex/delivery-flow
   ```

2. 创建 skill 软链接：
   ```bash
   mkdir -p ~/.codex/skills
   ln -s ~/.codex/delivery-flow ~/.codex/skills/delivery-flow
   ```

3. 重启 Codex。

### Windows

Windows 上可以使用 junction：

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills"
cmd /c mklink /J "$env:USERPROFILE\.codex\skills\delivery-flow" "$env:USERPROFILE\.codex\delivery-flow"
```

## 工作方式

Codex 会在会话启动时扫描 `~/.codex/skills/`，读取 `SKILL.md` frontmatter，
并在需要时按需加载 skill。`delivery-flow` 通过下面这条软链接暴露给 Codex：

```text
~/.codex/skills/delivery-flow -> ~/.codex/delivery-flow
```

安装完成后，这个 skill 提供一条稳定的 controller contract，并支持两个显式 mode：

- `superpowers-backed`
- `fallback`

## 使用方式

启动新的 Codex 会话后，可以直接要求它使用 `delivery-flow`，例如：

- “Use delivery-flow to keep this feature moving through spec, dev, review, and fix.”
- “Run this task with delivery-flow and stop only when owner input is required.”

Codex 通常会在两种情况下自动发现它：

- 你直接提到 `delivery-flow`
- 任务描述命中 `SKILL.md` 里的触发条件

## 安装验证

验证 skill 入口：

```bash
test -L ~/.codex/skills/delivery-flow
readlink -f ~/.codex/skills/delivery-flow
test -f ~/.codex/skills/delivery-flow/SKILL.md
```

验证仓库基线：

```bash
cd ~/.codex/delivery-flow
uv run pytest
```

当前期望基线：`27 passed`

## 默认 Runtime 路径

安装完成后，`delivery-flow` 默认会进入一条 runtime-backed controller loop：

- 显式选择 `superpowers-backed` / `fallback`
- runtime 自己推进 `spec -> plan -> dev -> review -> fix -> stop`
- run trace 记录证据，并生成 owner-visible terminal summary
- owner 不需要手工把阶段重新串起来

## 更新

```bash
cd ~/.codex/delivery-flow && git pull
uv run pytest
```

更新后建议重启 Codex，让下一次会话读取最新的 skill 元数据。

## 卸载

```bash
rm ~/.codex/skills/delivery-flow
rm -rf ~/.codex/delivery-flow
```

## 常见问题

### Skill 没有被发现

1. 检查软链接：`ls -la ~/.codex/skills/delivery-flow`
2. 检查 skill 入口：`test -f ~/.codex/skills/delivery-flow/SKILL.md`
3. 重启 Codex。skill discovery 发生在会话启动时。

### 测试跑不起来

1. 确认系统里有 `uv`
2. 在 `~/.codex/delivery-flow` 内运行 `uv sync`
3. 再运行 `uv run pytest`
