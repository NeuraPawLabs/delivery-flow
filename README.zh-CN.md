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
- 显式 `execution_strategy` 工作流状态：`subagent-driven`、`inline`、`unresolved`
- plan 之后由主 agent 持续推进执行，直到进入终止态
- execution-strategy 优先级固定为：`owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- 在 `superpowers-backed` 下，`subagent-driven` 会用 subagents 执行 plan 之后的 `dev/review/fix`，显式 `inline` 也仍然合法并在当前会话内执行；`fallback` 则原生保持同一套 owner-facing loop
- 如果 `execution_strategy=unresolved`，主 agent 可以在 plan 之后询问一次；否则不得再次打开通用执行方式选择
- owner 可以在运行中显式修改 execution strategy，新策略从下一个可调度 task 开始生效
- 一旦 `delivery-flow` 接管 plan 之后的工作流，上游通用模板不得覆盖已确定的 strategy
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

## Observability Service

- 现在所有项目都会写入同一个全局 observability 数据库
- 默认数据库路径会解析为 `DELIVERY_FLOW_HOME/observability/observability.db`
- 即使显式传入 `project_root`，也不得分叉到项目本地 observability 数据库
- 写路径仍然独立，runtime 不依赖 backend 是否启动
- backend 提供只读 observability API，并托管打包后的前端静态资源
- React UI 位于 `frontend/observability-ui`
- 开发时前端 dev server 和 Python backend 分开运行

本地开发常用流程：

```bash
cd /home/mm/workdir/code/python/delivery-flow/frontend/observability-ui
npm install
npm run dev
```

开发时前后端分离，生产环境则由 Python backend 直接提供构建后的 UI。

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
- plan 之后会显式维护 `execution_strategy`：`subagent-driven`、`inline`、`unresolved`
- execution-strategy 优先级固定为：`owner explicit instruction -> active run state -> repository-local preset -> delivery-flow default -> upstream generic behavior`
- plan 之后由主 agent 持续推进执行，直到进入终止态
- 在 `superpowers-backed` 下，`subagent-driven` 通过 subagents 执行 plan 之后的 `dev/review/fix`，显式 `inline` 则在当前会话内执行；`fallback` 保持同一套外部合约
- 如果 execution strategy 还未确定，主 agent 可以在 plan 之后询问一次
- 如果 execution strategy 已经确定，skill 不会再次打开通用执行方式选择
- 如果 owner 在运行中显式修改 execution strategy，新策略从下一个可调度 task 开始生效
- 一旦 `delivery-flow` 接管 plan 之后的工作流，上游通用模板不得覆盖已确定的 strategy
- runtime 会逐个执行 plan 里的 task，`fix` 完成后一定会重新进入 `review`
- task 边界不会停下；只有当前 task 严格通过后才会进入下一个 task
- 只要还存在 required changes、testing issues、maintainability issues，就不会被当成 `pass`
- `needs_owner_decision` 或 verification-unavailable 这类提前终止会直接返回给 owner
- 默认主用路径会直接进入 runtime
- final result 会带出 `completed_task_ids`、`pending_task_id`、`open_issue_summaries` 和 `owner_acceptance_required`
- workflow tests 已覆盖 pass、blocker recovery、same-blocker、needs-owner-decision、verification-unavailable
