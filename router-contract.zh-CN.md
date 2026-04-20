# Delivery-Flow Router Contract

[English Version](./router-contract.md)

本文档定义 `delivery-flow` 的 router-first contract。

## Router-First 角色

- `delivery-flow` 首先是 router-first 入口，然后才是执行 contract。
- 在每个新的用户回合，都要先判断是接管线程还是让行。
- 当当前回合属于持续交付线程时，应接管。
- 当只需要单一阶段时，应让行。

## 何时接管

- 已经存在 plan，且同一条线程还要继续推进
- review feedback 已到来，且同一条线程还要继续推进
- owner 在新的用户回合里继续已有线程
- 需要一个主 agent 持续推进线程直到 `pass` 或 owner input required

## 何时让行

- 这是全新线程上的 brainstorming-only 请求
- 这只是单一阶段的 plan-only 请求
- 这是不需要持续交付 ownership 的一次性请求
- 只需要单一阶段时，`delivery-flow` 应让行而不是接管

## 重判边界

- 在每个新的用户回合重判
- 不要在每个内部阶段边界重判
- 一旦已经接管，就保持在线程内，直到 terminal stop 或 owner 显式重定向
