# Observability Service Design

Date: 2026-04-19

## Context

`delivery-flow` is a global skill, not a per-project plugin. Observability therefore must not default to a separate database per project. All projects using the skill should write to one global observability store, and one independent backend service plus one UI should inspect that shared data set.

The current implementation already provides:

- runtime-side observability recording
- a sqlite schema for `project / run / task / loop / dispatch / event`
- a read-only query layer
- a minimal read-only JSON app object

What is still missing is the productized inspection layer:

- one global database location
- one independent backend service process
- one React UI panel
- a multi-project query model and routes

## Goals

- Use one global sqlite database for all `delivery-flow` runs across all projects.
- Keep runtime writes independent from backend availability.
- Provide one independent Python backend service that reads the global database.
- Provide one React + Vite UI for browsing all projects and their runs.
- Preserve the current workflow contract: observability remains read-only and does not control execution.

## Non-Goals

- authentication and authorization
- remote multi-user deployment concerns
- cross-machine aggregation
- alerting and notifications
- write APIs
- websocket streaming
- turning the backend into an execution controller

## Design Summary

The system is split into three layers:

1. Runtime writer
- every `delivery-flow` execution writes directly to the same global sqlite database
- writes happen regardless of whether the backend service is running

2. Read-only backend service
- one long-running Python process opens the same sqlite database in read-only mode
- the service exposes REST endpoints and serves built frontend assets

3. React UI
- a Vite-based frontend consumes the REST API
- development uses a dedicated frontend dev server
- production uses built assets served by the Python backend

## Global Data Location

Observability data belongs to the global skill, but it must not live inside the skill source/install directory.

The database should live in a user-level data directory resolved by this priority:

1. `DELIVERY_FLOW_HOME`
2. platform user data home
3. fallback `~/.local/share/delivery-flow/`

Recommended layout:

- `<data-home>/delivery-flow/observability/observability.db`
- `<data-home>/delivery-flow/observability/frontend-dist/`
- `<data-home>/delivery-flow/observability/logs/`

This keeps runtime data stable across skill upgrades and reinstalls.

## Data Model

The existing sqlite schema remains the base model:

- `projects`
- `runs`
- `tasks`
- `task_loops`
- `task_dispatches`
- `events`
- summary/projection tables

The key semantic change is not the schema itself but the lookup scope:

- one database contains many projects
- each run belongs to exactly one project
- UI and backend navigation starts at `projects`, not directly at `runs`

`project_root`, `project_name`, and `project_id` stay part of the recorded data so multiple repositories can coexist in the same database.

## Backend Service

### Responsibilities

- resolve the global database path
- open sqlite in read-only mode
- expose REST endpoints
- serve built frontend assets
- report health and schema readiness

### Boundaries

- backend never writes execution data
- backend never changes workflow state
- backend never becomes required for skill execution

### API Surface

- `GET /api/health`
- `GET /api/projects`
- `GET /api/projects/:project_id`
- `GET /api/projects/:project_id/runs`
- `GET /api/runs/:run_id`
- `GET /api/runs/:run_id/tasks`
- `GET /api/runs/:run_id/events`
- `GET /api/runs/:run_id/tasks/:task_id/loops`
- `GET /api/runs/:run_id/tasks/:task_id/dispatches`

### API Behavior

- all endpoints are read-only
- all responses are JSON
- empty database returns empty lists or explicit empty-state payloads
- schema missing or schema version mismatch returns explicit error payloads
- filtering should support:
  - mode
  - stop reason
  - time range
  - result limit

## UI Panel

### Stack

- React
- Vite

### Development Model

- frontend runs via Vite dev server
- backend runs separately as Python service
- Vite proxies `/api` to backend during development

### Production Model

- frontend is built to static assets
- backend serves the built assets directly

### Initial Screens

1. Projects list
- project name
- project root
- latest run time
- run count
- latest stop reason

2. Project detail
- run list for that project
- filters for mode, stop reason, time range

3. Run detail
- run summary cards
- owner-facing summary
- task list
- event timeline

4. Task detail area
- loops
- dispatches
- review/fix cycle visibility

### Interaction Rules

- polling refresh in the UI is sufficient for v1
- manual refresh is required
- URL must deep-link to project and run views
- empty state and backend-unavailable state must be explicit

## Runtime Integration

The runtime should keep auto-recording enabled by default, but the default destination must change from project-local storage to the global observability home.

Required behavior:

- if a custom recorder is provided, use it
- otherwise resolve the global default recorder automatically
- keep runtime writes short and synchronous
- do not require backend startup for successful execution

## Concurrency And Reliability

- sqlite runs in WAL mode
- runtime writes use short transactions
- backend uses read-only connections
- multiple concurrent project runs must be supported against the same database

This is acceptable because the backend is read-only and the runtime write pattern is append/projection oriented.

## Error Handling

The system must explicitly handle:

- database file does not exist
- schema not initialized
- schema version mismatch
- backend process unavailable
- partially recorded in-progress runs
- non-git projects

These should surface as explicit UI/backend states, not generic failures.

## Testing Strategy

### Backend

- global path resolution tests
- multi-project query tests
- API contract tests
- schema-missing and version-mismatch tests
- static asset serving smoke tests

### Frontend

- API client tests
- component rendering tests for project list and run detail
- empty/error/loading state tests

### End-to-End

- seed a shared sqlite database with multi-project data
- start backend
- load UI
- verify project list to run detail to task detail navigation

## Delivery Scope For V1

V1 is complete when all of the following are true:

- all runs write to one global sqlite database
- an independent backend service can inspect that database
- a React UI can browse projects, runs, tasks, loops, dispatches, and events
- the backend can serve the built UI
- runtime execution still succeeds with no backend running

## Open Decisions Already Resolved

- frontend stack: `React + Vite`
- dev workflow: frontend dev server separate from backend
- deployment model: built frontend assets served by Python backend
- storage model: one global database for all projects

## Implementation Notes

This design intentionally avoids introducing a broad CLI or a heavy platform architecture. The backend service should remain narrow, the UI should focus on observability only, and the runtime should continue treating observability as append/read-only support rather than workflow control.
