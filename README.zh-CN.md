# Delivery Flow

`delivery-flow` 是一个紧凑的 Codex skill 和控制器约定，用来把单条任务计划持续推进过
`spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`，而不是每一轮都重新断回 owner 手里。

[English README](./README.md) | [Codex 指南](./docs/README.codex.zh-CN.md) | [Claude/Cursor 指南](./docs/README.claude.zh-CN.md) | [OpenCode 指南](./docs/README.opencode.zh-CN.md)

## 当前状态

- 官方 skill 入口位于 `skills/delivery-flow/` 和 `skills/using-delivery-flow/`
- Codex 安装入口是 `~/.agents/skills/delivery-flow`
- Claude Code 和 Cursor 通过 `.claude-plugin` 与 `.cursor-plugin` 的 `SessionStart` bootstrap 接管路由
- OpenCode 会自动加载 `.opencode/plugins/delivery-flow.js`
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

## 平台安装

### Codex

直接告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

使用标准 skill clone 路径手动安装：

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/delivery-flow/skills ~/.agents/skills/delivery-flow
```

共享 skill 结构：

```text
~/.agents/skills/delivery-flow/
├── delivery-flow/
│   └── SKILL.md
└── using-delivery-flow/
    └── SKILL.md
```

### Claude Code 和 Cursor

安装插件、重启会话，让平台运行 delivery-flow 的 `SessionStart` bootstrap。

这段 bootstrap 不会替代 skill contract，它只负责把路由前置，让持续交付线程优先进入 `delivery-flow`。

### OpenCode

OpenCode 会把仓库作为 plugin 加载，并自动注册共享 `skills/` 目录。不需要 `AGENTS.md`。

## 文档导航

- [README.md](./README.md)
  英文人类概览。
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  中文人类向 Codex 安装与使用说明。
- [docs/README.codex.md](./docs/README.codex.md)
  英文人类向 Codex 安装与使用说明。
- [docs/README.claude.zh-CN.md](./docs/README.claude.zh-CN.md)
  中文人类向 Claude Code 与 Cursor 安装说明。
- [docs/README.claude.md](./docs/README.claude.md)
  英文人类向 Claude Code 与 Cursor 安装说明。
- [docs/README.opencode.zh-CN.md](./docs/README.opencode.zh-CN.md)
  中文人类向 OpenCode 安装与使用说明。
- [docs/README.opencode.md](./docs/README.opencode.md)
  英文人类向 OpenCode 安装与使用说明。
- [docs/contracts/selection-contract.zh-CN.md](./docs/contracts/selection-contract.zh-CN.md)
  中文 selection 阶段的优先级与边界约定。
- [docs/contracts/selection-contract.md](./docs/contracts/selection-contract.md)
  英文 selection contract。
- [docs/contracts/router-contract.zh-CN.md](./docs/contracts/router-contract.zh-CN.md)
  中文 router-first 接管与让行约定。
- [docs/contracts/router-contract.md](./docs/contracts/router-contract.md)
  英文 router-first contract。
- [docs/contracts/superpowers-backed.md](./docs/contracts/superpowers-backed.md)
  `superpowers-backed` backend 合约。
- [docs/contracts/fallback.md](./docs/contracts/fallback.md)
  `fallback` backend 合约。
- [docs/verification/verification-scenarios.md](./docs/verification/verification-scenarios.md)
  discovery、routing 与 execution 的验证场景。
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  给 agent 直接执行的安装文档。
- [skills/delivery-flow/SKILL.md](./skills/delivery-flow/SKILL.md)
  面向 AI 的执行 skill 合约。
- [skills/using-delivery-flow/SKILL.md](./skills/using-delivery-flow/SKILL.md)
  面向 AI 的根路由 skill 合约。

## 仓库结构

- `skills/`
  官方共享 skill 入口目录。
- `src/delivery_flow/controller.py`
  controller contract helper 和 public runtime launcher。
- `src/delivery_flow/runtime/`
  可执行的 runtime、stop rules 和状态推进。
- `src/delivery_flow/trace/`
  run trace 与 terminal evidence holder。
- `src/delivery_flow/adapters/`
  runtime-facing 的 `superpowers-backed` / `fallback` adapters。
- `docs/contracts/`
  面向人类与测试的 selection、routing 与 backend 合约。
- `docs/verification/`
  验证场景与行为 smoke 参考。
- `tests/`
  仓库测试基线。

## 技能选择指南

`delivery-flow` 应被视为持续交付线程里的顶层 orchestrator。

`delivery-flow` 是 router-first 的：在每个新的用户回合，都先判断应接管持续交付线程，还是在只需要单一阶段时让行。

| 场景 | 优先选择 |
| --- | --- |
| 新任务还需要需求澄清或方案讨论 | `brainstorming` |
| 设计已经批准，下一步只是产出 implementation plan | `writing-plans` |
| 已经有 plan，且工作可以线性执行后结束 | `executing-plans` |
| 即使已经有 plan，线程仍然是持续交付线程，并且很可能继续进入 review/fix | `delivery-flow` |
| owner 持续补充 review 问题，并希望同一个主 agent 继续推进 | `delivery-flow` |

关键规则：

- 即使已经有 plan，只要线程仍然是持续交付线程，就应优先 delivery-flow，而不是仅因为有 plan 就切到 `executing-plans`
- 只要存在或很可能存在 review/fix 持续循环，就应保持 `delivery-flow` 接管外层流程
- 不能仅因为 planning 完成就切换离开 `delivery-flow`
- 当新的用户回合是在继续已有持续交付线程时，应接管
- 当只需要单一阶段时，应让行，例如 brainstorming-only、plan-only 或一次性请求

## 常见误选模式

- Wrong: 已经有 plan，所以顶层 skill 应切换到 `executing-plans`
- Right: plan 虽然已经存在，但线程仍然需要持续 review/fix 推进，因此 `delivery-flow` 仍是顶层 orchestrator
- Wrong: brainstorming 或 planning 结束后，外层流程应切给别的 process skill
- Right: 当同一条线程仍需要持续交付 ownership 时，`brainstorming`、`writing-plans`、`executing-plans` 都只是阶段性或从属 workflow

这意味着：即使已经有 plan，只要还是持续交付线程，顶层仍优先 delivery-flow。

## 验证方式

```bash
cd ~/.codex/delivery-flow
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
