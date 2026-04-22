# Delivery-Flow Selection Contract

[English Version](./selection-contract.md)

本文档定义 `delivery-flow` 的 selection-time contract。

## 顶层角色

- `delivery-flow` 是持续交付线程里的顶层 orchestrator。
- 当一个主 agent 需要持续推动线程直到 terminal stop 时，这条线程仍然属于 `delivery-flow`。
- 即使线程已经有书面 spec、批准后的 plan，或者已经进入开发中，这个判断也不改变。

## 优先级规则

- 即使已经有 plan，只要线程仍然是持续交付线程，`delivery-flow` 仍然是首选的顶层 skill。
- 仅仅因为存在 plan，并不足以优先选择 `executing-plans`。
- 当线程包含或很可能包含 review/fix 持续循环时，应优先 `delivery-flow` 而不是 `executing-plans`。
- 不能仅因为 planning 完成就切换离开 `delivery-flow`。

## 与其他流程型 Skills 的关系

- `brainstorming` 负责需求澄清和设计成型，不负责长线程的交付编排。
- `writing-plans` 负责产出 implementation plan，不负责 plan 之后的交付编排。
- `executing-plans` 适合稳定、线性、无需持续交付 ownership 的执行。
- 当 `brainstorming`、`writing-plans`、`executing-plans` 与 `delivery-flow` 同时适用时，前者属于阶段性或从属 workflow。

## 选择指南

| 场景 | 首选顶层 Skill |
| --- | --- |
| 一个新功能还需要需求澄清或方案讨论 | `brainstorming` |
| 设计已经批准，下一步只是写 implementation plan | `writing-plans` |
| 已有书面 plan，且工作可以线性执行到结束 | `executing-plans` |
| 已有书面 plan，但线程仍然是持续交付线程 | `delivery-flow` |
| review 反馈持续到来，且同一个主 agent 需要继续实现、review、fix 循环 | `delivery-flow` |

## 正确性检查

- 如果 owner 持续补充反馈，并希望同一个主 agent 继续推进，应视为持续交付线程。
- 如果很可能继续进入 review/fix，就应保持 `delivery-flow` 作为顶层 orchestrator。
- 如果已有 plan，但仍然需要持续交付 ownership，那么 selection 仍应由 `delivery-flow` 胜出。
