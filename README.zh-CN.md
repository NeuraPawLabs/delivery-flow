# Delivery Flow

`delivery-flow` 是一个给 Codex 使用的 skill 和控制器约定，用来把单条任务计划持续推进过
`spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`，而不是每一轮都重新断回 owner 手里。

[English README](./README.md) | [Codex 指南](./docs/README.codex.zh-CN.md) | [Codex Guide](./docs/README.codex.md)

## 当前状态

- 仓库内已经有真实 skill 入口：`SKILL.md`
- 本机 skill 安装入口：`~/.codex/skills/delivery-flow`
- 默认主用路径现在会进入可执行的 stage-2 runtime
- 默认主用路径现在会在 plan 之后按 task 逐个推进 runtime
- real-task runtime validation 已通过
- 当前仓库验证基线：`uv run pytest` 成功完成，且全部仓库测试通过

## 核心能力

- 显式 mode 选择：`superpowers-backed` / `fallback`
- controller 自己归一 review 结果：`pass / blocker / needs_owner_decision`
- controller 自己定义 blocker identity
- task-loop 证据会暴露完成任务、待处理任务、open issues 和 owner acceptance 状态
- 包含显式的 `running_finalize` 阶段，然后才进入 `waiting_for_owner`
- task 级别的 `pass` 只会推进到下一个 task，只有整份 plan 成功后才会进入 `finalize`
- runtime/trace 自己产出 owner-visible 的 stop-and-wait 收口

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
  英文项目概览。
- [docs/README.codex.zh-CN.md](./docs/README.codex.zh-CN.md)
  中文 Codex 安装与使用说明。
- [docs/README.codex.md](./docs/README.codex.md)
  英文 Codex 安装与使用说明。
- [.codex/INSTALL.md](./.codex/INSTALL.md)
  给 agent 直接执行的安装文档。
- [SKILL.md](./SKILL.md)
  Codex 加载时读取的 skill 合约。
- [docs/skill-validation-matrix.md](./docs/skill-validation-matrix.md)
  用最小矩阵把验证场景映射到仓库内测试与证据。
- [docs/stage-2-real-task-validation.md](./docs/stage-2-real-task-validation.md)
  已发布的 runtime-backed 验证证据。

## 仓库结构

- `SKILL.md`
  skill 主入口。
- `src/delivery_flow/controller.py`
  controller contract helper 和 public runtime launcher。
- `src/delivery_flow/runtime/`
  可执行的 stage-2 runtime、stop rules 和状态推进。
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

这一版已经证明了以下几点：

- skill 可以被 Codex 安装并发现
- controller runtime 已经能执行 `spec -> plan -> task-by-task dev/review/fix -> finalize -> wait`
- runtime 会逐个执行 plan 里的 task，只有当前 task review 通过后才会进入下一个 task
- `needs_owner_decision` 或 verification-unavailable 这类提前终止会直接返回，不会进入 `running_finalize`
- 默认主用路径会直接进入 runtime
- final result 会带出 `completed_task_ids`、`pending_task_id`、`open_issue_summaries` 和 `owner_acceptance_required`
- 在整份 plan 成功时，`owner_acceptance_required` 由 finalization result 决定，可能是 `True` 或 `False`
- workflow tests 已覆盖 pass、blocker recovery、same-blocker、needs-owner-decision、verification-unavailable
- 仓库内已经发布一条 runtime-backed validation 证据
- reviewer 的 re-review 已确认 runtime-backed 连续驱动成立

## 下一轮可继续做的事

后续不再是“补完第一版”，而是进入下一轮目标，例如：

- 更大的真实任务验证
- workflow 证据发布
- 更严格的 backend parity 强化
