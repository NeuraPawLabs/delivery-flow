# Delivery-Flow Router Contract

This document defines the router-first contract for `delivery-flow`.

## Router-First Role

- `delivery-flow` is router-first before it is an execution contract.
- On each new user turn, decide whether to take ownership of the thread or yield.
- Take ownership when the turn belongs to an ongoing delivery thread.
- Yield when only a single phase is needed.

## When To Take Ownership

- a plan already exists and the same thread must continue
- review feedback has arrived and the same thread must continue
- the owner is continuing an existing thread on a new user turn
- one main agent must keep the same thread moving until `pass` or owner input is required

## When To Yield

- the task is brainstorming-only for a brand-new thread
- the task is plan-only for a single phase
- the task is a one-shot request without ongoing delivery ownership
- only a single phase is needed, so `delivery-flow` should yield

## Re-Evaluation Boundary

- re-evaluate on each new user turn
- do not re-route on every internal phase boundary
- once ownership is taken, stay inside `delivery-flow` until a terminal stop or explicit owner redirect
