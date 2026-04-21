# Delivery Flow for OpenCode

这是给 OpenCode 使用者看的安装与使用说明。

[English Version](./README.opencode.md)

## 快速开始

1. 在 OpenCode 中打开这个仓库。
2. 让 OpenCode 从 `.opencode/plugins/` 自动加载 `.opencode/plugins/delivery-flow.js`。
3. 在仓库里启动一个新的会话。

## 插件会做什么

- 通过 OpenCode 的 `config hook` 注册仓库 worktree 下的 `skills/` 目录
- 通过 `experimental.chat.system.transform` 注入一段 routing-only bootstrap
- 让启动路由优先指向 `using-delivery-flow`
- 保持 bootstrap 只负责路由判断，不内联后续执行语义

## 相关文件

- `package.json`
- `.opencode/plugins/delivery-flow.js`
- `.opencode/INSTALL.md`

## 验证

检查 package 入口：

```bash
node -e "console.log(JSON.parse(require('node:fs').readFileSync('package.json', 'utf8')).main)"
```

检查插件源码：

```bash
grep -n "config(config)\\|experimental.chat.system.transform\\|using-delivery-flow\\|routing-only" .opencode/plugins/delivery-flow.js
```

Windows PowerShell 可以用：

```powershell
Select-String -Path .opencode/plugins/delivery-flow.js -Pattern "config\\(config\\)|experimental\\.chat\\.system\\.transform|using-delivery-flow|routing-only"
```

检查共享 skill 文件：

```bash
test -f skills/using-delivery-flow/SKILL.md
test -f skills/delivery-flow/SKILL.md
```

Windows PowerShell 可以用：

```powershell
Test-Path skills/using-delivery-flow/SKILL.md
Test-Path skills/delivery-flow/SKILL.md
```

运行本任务对应的测试切片：

```bash
uv run pytest tests/test_platform_bootstrap.py -q
```

再做一次真实 OpenCode 会话的 smoke check：

```text
What do the using-delivery-flow and delivery-flow skills do in this project?
```

期望结果：OpenCode 能从仓库本地 `skills/` 目录识别出这两个 skill，并把
`using-delivery-flow` 解释为 routing-only 的启动路由层。

## 行为约束

- `using-delivery-flow` 是根路由 skill
- 启动 bootstrap 必须保持 routing-only
- 插件不应内联后续 workflow 的执行语义

更简短的安装说明见 `.opencode/INSTALL.md`。
