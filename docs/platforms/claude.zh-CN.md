# Delivery Flow for Claude Code and Cursor

这是给 Claude Code 和 Cursor 使用者看的中文安装与使用说明。

[English Version](./claude.md)

## 快速开始

1. 在 Claude Code 或 Cursor 中打开这个仓库。
2. 把整个仓库作为插件包安装，这样根目录下的 `.claude-plugin`、
   `.cursor-plugin`、`hooks/` 和 `skills/` 路径才能保持有效。
3. 重启会话，让 `SessionStart` 再执行一次。

## 安装内容

- 仓库根目录本身就是 Claude Code 和 Cursor 的安装面
- `.claude-plugin/plugin.json` 提供 Claude Code 的插件元数据
- `.cursor-plugin/plugin.json` 提供 Cursor 的插件元数据
- `hooks/hooks.json` 负责 Claude Code 的 `SessionStart`
- `hooks/hooks-cursor.json` 负责 Cursor 的 `sessionStart`
- `hooks/session-start` 会输出一段指向 `using-delivery-flow` 的路由 bootstrap
- `skills/` 会作为共享 skill 目录保留在安装根目录

## Bootstrap 合约

- bootstrap 只在 `SessionStart` 运行
- 它不会替代 `delivery-flow` 的 skill contract
- 它只是把路由前置，让持续交付线程优先进入 `delivery-flow`
- 单一阶段任务仍然应该让行给普通 skill 生态

## 验证

检查插件清单：

```bash
test -f .claude-plugin/plugin.json
test -f .cursor-plugin/plugin.json
```

检查 hook 配置：

```bash
grep -n "SessionStart\\|sessionStart\\|using-delivery-flow" hooks/hooks.json hooks/hooks-cursor.json hooks/session-start
```

运行聚焦测试切片：

```bash
uv run pytest tests/test_platform_bootstrap.py -q
```

启动一个全新的会话，确认启动路由会在正常任务执行前提到
`using-delivery-flow`。

## 说明

- bootstrap 是 routing-only 的
- 真正的 runtime contract 仍然在 `delivery-flow`
- 不需要 `AGENTS.md`
