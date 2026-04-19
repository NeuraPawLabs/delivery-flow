# Delivery Flow

`delivery-flow` 是一个紧凑的 Codex skill 和控制器约定，用来把单条任务计划持续推进过
`spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`，而不是每一轮都重新断回 owner 手里。

[English README](./README.md) | [Codex 指南](./docs/README.codex.zh-CN.md) | [Codex Guide](./docs/README.codex.md)

## 当前状态

- 仓库内已经有真实 skill 入口：`SKILL.md`
- 本机 skill 安装入口：`~/.codex/skills/delivery-flow`
- 默认主用路径会直接进入 runtime
- plan 之后会按 task 逐个推进，直到进入终止态
- 当前仓库验证基线：`uv run pytest` 成功完成，且全部仓库测试通过

## 核心能力

- 显式 mode 选择：`superpowers-backed` / `fallback`
- plan 之后由主 agent 持续推进执行，直到进入终止态
- `superpowers-backed` 会用 subagents 执行 plan 之后的 `dev/review/fix`；`fallback` 则原生保持同一套 owner-facing loop
- `fix` 不是终点，必须重新进入 `review`，也不会在 task 边界停下
- 严格 `pass`：只要还存在 required changes、testing issues 或 maintainability issues，就不能算通过
- task-loop 证据会暴露完成任务、待处理任务、open issues 和 owner acceptance 状态

## 给 Codex 的快速安装方式

直接告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

当前机器手动安装：

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/code/python/delivery-flow ~/.codex/skills/delivery-flow
```

安装后的 skill 入口：

```text
~/.codex/skills/delivery-flow/SKILL.md
```

## 文档导航

- [README.md](./README.md)
  英文概览。
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  中文 Codex 安装与使用说明。
- [docs/README.codex.md](./docs/README.codex.md)
  英文 Codex 安装与使用说明。
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  给 agent 直接执行的安装文档。
- [SKILL.md](./SKILL.md)
  Codex 加载时读取的 skill 合约。

## 仓库结构

- `SKILL.md`
  skill 主入口。
- `src/delivery_flow/controller.py`
  controller contract helper 和 public runtime launcher。
- `src/delivery_flow/runtime/`
  可执行的 runtime、stop rules 和状态推进。
- `src/delivery_flow/trace/`
  run trace 与 terminal evidence holder。
- `src/delivery_flow/adapters/`
  runtime-facing 的 `superpowers-backed` / `fallback` adapters。
- `superpowers-backed.md`
  `superpowers` backend 合约。
- `fallback.md`
  fallback backend 合约。
- `verification-scenarios.md`
  双 mode 一致性场景。
- `tests/`
  仓库测试基线。

## 验证方式

```bash
cd /home/mm/workdir/code/python/delivery-flow
uv run pytest
```

期望结果：`uv run pytest` 成功完成，且全部仓库测试通过。

## 当前已证明的范围

这一版聚焦证明以下几点：

- skill 可以被 Codex 安装并发现
- controller runtime 已经能执行 `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
- plan 之后由主 agent 持续推进执行，直到进入终止态
- 在 `superpowers-backed` 下，plan 之后的 `dev/review/fix` 通过 subagents 执行；`fallback` 保持同一套外部合约
- runtime 会逐个执行 plan 里的 task，`fix` 完成后一定会重新进入 `review`
- task 边界不会停下；只有当前 task 严格通过后才会进入下一个 task
- 只要还存在 required changes、testing issues、maintainability issues，就不会被当成 `pass`
- `needs_owner_decision` 或 verification-unavailable 这类提前终止会直接返回给 owner
- 默认主用路径会直接进入 runtime
- final result 会带出 `completed_task_ids`、`pending_task_id`、`open_issue_summaries` 和 `owner_acceptance_required`
- workflow tests 已覆盖 pass、blocker recovery、same-blocker、needs-owner-decision、verification-unavailable
