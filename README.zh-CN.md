# Delivery Flow

`delivery-flow` 是一个紧凑的跨平台共享 agent skill 入口与控制器约定，
用来把单条任务计划持续推进过
`spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`，而不是每一轮都重新断回 owner 手里。

[English README](./README.md) | [架构说明](./docs/architecture.zh-CN.md) | [Codex 指南](./docs/platforms/codex.zh-CN.md) | [Claude/Cursor 指南](./docs/platforms/claude.zh-CN.md) | [OpenCode 指南](./docs/platforms/opencode.zh-CN.md)

docs/ 只放给人类看的文档；skills/ 是给 agent 读取的，并存放 skill 入口和 supporting references。

平台能力分层：

- Codex 只会以 discovery-only 方式暴露共享 skill 树，不会注入 session-start bootstrap
- Claude Code、Cursor、OpenCode 都是 bootstrap-capable 平台，会在 before any response 前置共享根路由合约

共享定位：这个仓库已经不是 Codex-only。它发布的是一套跨平台共享
skill surface，平台差异只体现在 discovery-only 与 bootstrap-capable
两种启动能力上。Codex 仍然是 discovery-only，并且没有
session-start bootstrap parity。用平台简称来说，仍然可以理解为
Codex 与 Claude/Cursor/OpenCode 的能力分层。Codex is
discovery-only。Claude Code, Cursor, and OpenCode are
bootstrap-capable。

## 当前状态

- 官方 skill 入口位于 `skills/delivery-flow/` 和 `skills/using-delivery-flow/`
- Codex 安装入口是 `~/.agents/skills/delivery-flow`，当前属于 discovery-only 模式
- Claude Code 和 Cursor 属于 bootstrap-capable 平台，并通过 `.claude-plugin` 与 `.cursor-plugin` 的 `SessionStart` bootstrap 接管路由
- OpenCode 属于 bootstrap-capable 平台，并会自动加载 `.opencode/plugins/delivery-flow.js`
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

`docs/` 放人类文档，`skills/` 放给 agent 使用的 skill contract 与 supporting references。

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

Claude Code 和 Cursor 属于 bootstrap-capable 平台。它们会在 before any response 之前注入 strong root-routing bootstrap，在每个新的用户回合先判断是否该接管持续交付线程，并且只有请求确实是 single-phase 时才让行。

### OpenCode

OpenCode 会把仓库作为 plugin 加载，并自动注册共享 `skills/` 目录。不需要 `AGENTS.md`。

OpenCode 也属于 bootstrap-capable 平台。它会在 before any response 之前追加 strong root-routing bootstrap，让 review/fix continuation 继续留在 `delivery-flow`，而 single-phase work 仍然让行。

## 人类文档

- [README.md](./README.md)
  英文人类概览。
- [docs/architecture.zh-CN.md](./docs/architecture.zh-CN.md)
  中文架构与调用流程说明。
- [docs/architecture.md](./docs/architecture.md)
  英文架构与调用流程说明。
- [docs/platforms/codex.zh-CN.md](./docs/platforms/codex.zh-CN.md)
  中文人类向 Codex 安装与使用说明。
- [docs/platforms/codex.md](./docs/platforms/codex.md)
  英文人类向 Codex 安装与使用说明。
- [docs/platforms/claude.zh-CN.md](./docs/platforms/claude.zh-CN.md)
  中文人类向 Claude Code 与 Cursor 安装说明。
- [docs/platforms/claude.md](./docs/platforms/claude.md)
  英文人类向 Claude Code 与 Cursor 安装说明。
- [docs/platforms/opencode.zh-CN.md](./docs/platforms/opencode.zh-CN.md)
  中文人类向 OpenCode 安装与使用说明。
- [docs/platforms/opencode.md](./docs/platforms/opencode.md)
  英文人类向 OpenCode 安装与使用说明。

## AI Skill 文件

- [skills/delivery-flow/SKILL.md](./skills/delivery-flow/SKILL.md)
  面向 AI 的执行 skill 合约。
- [skills/delivery-flow/selection-contract.md](./skills/delivery-flow/selection-contract.md)
  selection supporting contract。
- [skills/delivery-flow/router-contract.md](./skills/delivery-flow/router-contract.md)
  router-first supporting contract。
- [skills/delivery-flow/superpowers-backed.md](./skills/delivery-flow/superpowers-backed.md)
  `superpowers-backed` supporting backend 合约。
- [skills/delivery-flow/fallback.md](./skills/delivery-flow/fallback.md)
  `fallback` supporting backend 合约。
- [skills/delivery-flow/verification-scenarios.md](./skills/delivery-flow/verification-scenarios.md)
  execution skill 的 supporting verification 场景。
- [skills/using-delivery-flow/SKILL.md](./skills/using-delivery-flow/SKILL.md)
  面向 AI 的根路由 skill 合约。
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  给 agent 直接执行的安装文档。

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
- `docs/platforms/`
  面向人类的 Codex、Claude Code、Cursor 与 OpenCode 安装说明。
- `docs/architecture.zh-CN.md`
  面向人类的架构说明，解释 markdown contract 与 runtime 的协作流程。
- `skills/delivery-flow/`
  执行 skill 入口以及面向 AI 的 supporting contract / verification 文档。
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

- 共享 skill surface 可以在已支持的平台上安装；其中 Codex 走
  discovery-only 接线，Claude Code、Cursor、OpenCode 还会补充
  bootstrap-capable 的启动路由能力
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
