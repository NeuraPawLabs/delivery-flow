---
name: using-delivery-flow
description: Use when starting a conversation or continuing an ongoing delivery thread where continuous delivery orchestration may be needed; routes ongoing delivery threads into `delivery-flow` and yields single-phase work to normal stage-specific skills.
---

# Using Delivery Flow

This is a thin routing skill.

Use it at the root of a conversation to decide whether the thread should route into `delivery-flow`.

Route into `delivery-flow` when the user is continuing an ongoing delivery thread and one main agent should keep ownership across phases.

Yield to the normal stage-specific skills when the request is only a single phase such as brainstorming, writing a plan, executing one bounded task, or handling one review pass.

Do not duplicate `delivery-flow` execution semantics here. This skill only decides whether to hand off to `delivery-flow` or yield to the normal skill ecosystem.
