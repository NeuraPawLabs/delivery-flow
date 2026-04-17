# Delivery Flow

`delivery-flow` 是一个给 Codex 使用的 skill 和控制器约定，用来把单条任务持续推进过
`spec -> dev -> review -> fix -> stop`，而不是每一轮都重新断回 owner 手里。

[English README](./README.md) | [Codex 指南](./docs/README.codex.zh-CN.md) | [Codex Guide](./docs/README.codex.md)

## 当前状态

- 仓库内已经有真实 skill 入口：`SKILL.md`
- 本机 skill 安装入口：`~/.codex/skills/delivery-flow`
- 默认主用路径现在会进入可执行的 stage-2 runtime
- real-task runtime validation 已通过
- 当前仓库验证基线：`uv run pytest` -> `27 passed`

## 核心能力

- 显式 mode 选择：`superpowers-backed` / `fallback`
- controller 自己归一 review 结果：`pass / blocker / needs_owner_decision`
- controller 自己定义 blocker identity
- runtime/trace 自己产出 owner-visible 的 stop-and-wait 收口

## 给 Codex 的快速安装方式

直接告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/NeuraPawLabs/delivery-flow/main/.codex/INSTALL.md
```

当前机器手动安装：

```bash
mkdir -p ~/.codex/skills
ln -s /home/mm/workdir/projects/delivery-flow ~/.codex/skills/delivery-flow
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
cd /home/mm/workdir/projects/delivery-flow
uv run pytest
```

当前基线：`27 passed`

## 当前已证明的范围

这一版已经证明了以下几点：

- skill 可以被 Codex 安装并发现
- controller runtime 已经能执行 `spec -> plan -> dev -> review -> fix -> stop`
- 默认主用路径会直接进入 runtime
- workflow tests 已覆盖 pass、blocker recovery、same-blocker、needs-owner-decision、verification-unavailable
- 仓库内已经发布一条 runtime-backed validation 证据
- reviewer 的 re-review 已确认 runtime-backed 连续驱动成立

## 下一轮可继续做的事

后续不再是“补完第一版”，而是进入下一轮目标，例如：

- 更大的真实任务验证
- workflow 证据发布
- 更严格的 backend parity 强化
