# Delivery Flow for Codex

[English](README.codex.md) | [简体中文](README.codex.zh-CN.md)

这是 `delivery-flow` 在 Codex 中的安装与使用说明。

## 快速安装

告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

## 手动安装

### 前置条件

- OpenAI Codex
- Git
- `uv`，用于本地验证

### 安装步骤

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

Windows 下可用 junction 代替 symlink：

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills"
cmd /c mklink /J "$env:USERPROFILE\.codex\skills\delivery-flow" "$env:USERPROFILE\.codex\delivery-flow"
```

## 工作方式

Codex 会在 session 启动时扫描 `~/.codex/skills/`，读取 `SKILL.md`
frontmatter，并在需要时加载对应 skill。`delivery-flow` 的可见路径是：

```text
~/.codex/skills/delivery-flow -> ~/.codex/delivery-flow
```

安装完成后，这个 skill 会暴露一套统一的 controller contract，并支持两种显式
mode：

- `superpowers-backed`
- `fallback`

## 使用方式

启动一个新的 Codex session，然后给出适合连续交付编排的任务，例如：

- “Use delivery-flow to keep this feature moving through spec, dev, review, and fix.”
- “Run this task with delivery-flow and stop only when owner input is required.”

Codex 会在这些情况下自动发现它：

- 你直接提到 `delivery-flow`
- 当前任务匹配 `SKILL.md` 的描述

## 验证安装

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

预期基线：`11 passed`

## 更新

```bash
cd ~/.codex/delivery-flow && git pull
uv run pytest
```

更新后重启 Codex，这样新的 session 会读取到最新的 skill 元数据。

## 卸载

```bash
rm ~/.codex/skills/delivery-flow
rm -rf ~/.codex/delivery-flow
```

## 故障排查

### 找不到 skill

1. 确认软链接存在：`ls -la ~/.codex/skills/delivery-flow`
2. 确认入口文件存在：`test -f ~/.codex/skills/delivery-flow/SKILL.md`
3. 重启 Codex。skill discovery 发生在 session 启动时。

### 测试跑不起来

1. 确认 `uv` 已安装。
2. 在 `~/.codex/delivery-flow` 里执行 `uv sync`。
3. 重新执行 `uv run pytest`。
