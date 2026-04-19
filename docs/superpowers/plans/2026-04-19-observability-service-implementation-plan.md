# Observability Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-shaped observability inspection system for `delivery-flow` with one global sqlite database, one independent Python backend service, and one React + Vite UI.

**Architecture:** Keep the runtime write path local-first and backend-independent, but change the default storage target from project-local sqlite to one global observability home. Expand the read layer into a multi-project REST backend, then add a separately developed React UI whose built assets are packaged and served by the Python backend.

**Tech Stack:** Python 3.11+, stdlib `sqlite3`, stdlib `http.server`, stdlib `importlib.resources`, dataclasses, pytest, React 18, TypeScript, Vite, Vitest, Playwright

---

## File Structure

- Create: `tests/test_observability_config.py`
  Path-resolution contract tests for `DELIVERY_FLOW_HOME`, XDG fallback, and global sqlite target.
- Modify: `src/delivery_flow/observability/config.py`
  Shared global observability home resolution and backend/runtime path helpers.
- Modify: `src/delivery_flow/observability/sqlite_store.py`
  Schema upgrade to explicit per-run `event_index`, plus migration/version handling.
- Modify: `src/delivery_flow/observability/recorder.py`
  Global recorder construction and stable `event_index` assignment.
- Modify: `src/delivery_flow/controller.py`
  Default skill path must always resolve to the one global database.
- Modify: `tests/test_observability_sqlite.py`
  Schema and query assertions for `event_index` and global path semantics.
- Modify: `tests/test_default_use_path.py`
  Default skill execution should write to the global database, not CWD-local storage.
- Modify: `src/delivery_flow/observability/queries.py`
  Multi-project query API with ordering and `limit`/`offset`.
- Modify: `src/delivery_flow/observability/backend.py`
  JSON route contract for `/api/projects`, `/api/runs`, task/loop/dispatch/event endpoints.
- Create: `src/delivery_flow/observability/service.py`
  Long-running HTTP service that serves JSON API and packaged frontend assets.
- Create: `tests/test_observability_service.py`
  Service-level tests for API/static serving, health, and missing-schema behavior.
- Create: `scripts/build_observability_ui.py`
  Copies built Vite assets into the Python package resource directory.
- Create: `src/delivery_flow/observability/web_dist/.gitkeep`
  Packaged static asset destination checked into the wheel path.
- Modify: `pyproject.toml`
  Include packaged frontend assets in wheel builds.
- Modify: `tests/test_packaging_smoke.py`
  Assert wheel/service package can serve built UI assets.
- Create: `frontend/observability-ui/package.json`
  Frontend dependency and script entrypoint.
- Create: `frontend/observability-ui/tsconfig.json`
  TypeScript compiler settings.
- Create: `frontend/observability-ui/vite.config.ts`
  Vite dev/build config with `/api` proxy.
- Create: `frontend/observability-ui/index.html`
  Vite HTML shell.
- Create: `frontend/observability-ui/src/main.tsx`
  React bootstrap.
- Create: `frontend/observability-ui/src/App.tsx`
  Router shell and layout.
- Create: `frontend/observability-ui/src/api.ts`
  Typed fetch helpers for backend endpoints.
- Create: `frontend/observability-ui/src/types.ts`
  Shared frontend response types.
- Create: `frontend/observability-ui/src/pages/ProjectsPage.tsx`
  Projects list view.
- Create: `frontend/observability-ui/src/pages/ProjectRunsPage.tsx`
  Project-level run list with filters.
- Create: `frontend/observability-ui/src/pages/RunDetailPage.tsx`
  Run/task/event detail view.
- Create: `frontend/observability-ui/src/components/*.tsx`
  Small focused UI pieces such as status badges, data tables, and empty/error states.
- Create: `frontend/observability-ui/src/styles.css`
  Frontend styling.
- Create: `frontend/observability-ui/src/__tests__/api.test.ts`
  API client tests.
- Create: `frontend/observability-ui/src/__tests__/pages.test.tsx`
  Component rendering tests.
- Create: `frontend/observability-ui/playwright.config.ts`
  End-to-end smoke configuration.
- Create: `frontend/observability-ui/tests/e2e/observability-ui.spec.ts`
  Projects -> runs -> run detail smoke test.
- Modify: `README.md`
  Add observability service overview and dev/build usage.
- Modify: `README.zh-CN.md`
  Chinese documentation for the same flow.
- Modify: `tests/test_docs_contract.py`
  Lock docs to the new observability service entrypoints and verification commands.

### Task 1: Move Observability To One Global Database And Add Stable Event Ordering

**Files:**
- Create: `tests/test_observability_config.py`
- Modify: `src/delivery_flow/observability/config.py`
- Modify: `src/delivery_flow/observability/sqlite_store.py`
- Modify: `src/delivery_flow/observability/recorder.py`
- Modify: `src/delivery_flow/controller.py`
- Modify: `tests/test_observability_sqlite.py`
- Modify: `tests/test_default_use_path.py`

- [ ] **Step 1: Write the failing config and schema tests**

```python
def test_global_observability_home_uses_delivery_flow_home_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "delivery-flow-home"))

    home = resolve_observability_home()
    db_path = resolve_global_observability_db_path()

    assert home == (tmp_path / "delivery-flow-home")
    assert db_path == home / "observability" / "observability.db"


def test_events_table_exposes_stable_per_run_event_index(tmp_path: Path) -> None:
    recorder = build_sqlite_recorder(
        db_path=tmp_path / "observability.db",
        project_root=tmp_path / "project-a",
        skill_name="delivery-flow",
    )
    run_id = recorder.record_run_started(mode="superpowers-backed")
    recorder.record_run_completed(
        run_id=run_id,
        final_state="waiting_for_owner",
        stop_reason="pass",
        owner_acceptance_required=False,
    )

    snapshot = recorder.query_debug_snapshot()

    assert [event["event_index"] for event in snapshot["events"]] == [1, 2]
```

```python
def test_run_delivery_flow_writes_to_global_observability_home_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "delivery-flow-home"))

    result = run_delivery_flow(
        payload={"ticket": 901, "goal": "global observability home"},
        provider=FakeProvider(review_result="approved"),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stop_reason is StopReason.PASS
    assert resolve_global_observability_db_path().is_file()
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_observability_config.py tests/test_observability_sqlite.py tests/test_default_use_path.py -q`
Expected: FAIL because global-path helpers and `event_index` do not exist yet.

- [ ] **Step 3: Implement the global-path helpers, schema upgrade, and default recorder path**

```python
def resolve_observability_home() -> Path:
    override = os.environ.get("DELIVERY_FLOW_HOME")
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "delivery-flow"
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "delivery-flow"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "delivery-flow"


def resolve_global_observability_db_path() -> Path:
    return resolve_observability_home() / "observability" / "observability.db"
```

```python
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    event_index INTEGER NOT NULL,
    task_id TEXT,
    loop_id TEXT,
    dispatch_id TEXT,
    event_kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
)
```

```python
next_index = conn.execute(
    "SELECT COALESCE(MAX(event_index), 0) + 1 FROM events WHERE run_id = ?",
    (run_id,),
).fetchone()[0]

conn.execute(
    """
    INSERT INTO events (
        event_id, run_id, event_index, task_id, loop_id, dispatch_id, event_kind, payload_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        uuid4().hex,
        run_id,
        next_index,
        task_id,
        loop_id,
        dispatch_id,
        event_kind,
        json.dumps(payload, sort_keys=True),
        _utc_now(),
    ),
)
```

```python
def _resolve_default_recorder(recorder: ObservabilityRecorder | None) -> ObservabilityRecorder:
    if recorder is not None:
        return recorder

    project_root = Path.cwd()
    return build_sqlite_recorder(
        db_path=resolve_global_observability_db_path(),
        project_root=project_root,
        skill_name="delivery-flow",
    )
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `uv run pytest tests/test_observability_config.py tests/test_observability_sqlite.py tests/test_default_use_path.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_observability_config.py src/delivery_flow/observability/config.py src/delivery_flow/observability/sqlite_store.py src/delivery_flow/observability/recorder.py src/delivery_flow/controller.py tests/test_observability_sqlite.py tests/test_default_use_path.py
git commit -m "feat: move observability to global database"
```

### Task 2: Expand The Query Layer And JSON API To Multi-Project Reads

**Files:**
- Modify: `src/delivery_flow/observability/queries.py`
- Modify: `src/delivery_flow/observability/backend.py`
- Modify: `tests/test_observability_backend.py`

- [ ] **Step 1: Write the failing query and API tests**

```python
def test_queries_list_projects_and_project_runs_in_stable_order(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.db"
    seed_multi_project_observability_db(db_path)
    queries = ObservabilityQueries(_ReadOnlyStore(db_path=db_path))

    projects = queries.list_projects(limit=10, offset=0)
    runs = queries.list_project_runs(project_id="project-b", limit=10, offset=0)

    assert [project["project_name"] for project in projects] == ["project-b", "project-a"]
    assert runs[0]["started_at"] >= runs[1]["started_at"]


def test_backend_serves_projects_run_details_and_events(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.db"
    run_id = seed_multi_project_observability_db(db_path)
    app = build_observability_app(db_path)

    projects = app.handle_json("GET", "/api/projects?limit=20&offset=0")
    run_detail = app.handle_json("GET", f"/api/runs/{run_id}")
    events = app.handle_json("GET", f"/api/runs/{run_id}/events?limit=100&offset=0")

    assert projects["items"]
    assert run_detail["run_id"] == run_id
    assert [event["event_index"] for event in events["items"]] == [1, 2, 3]
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_observability_backend.py -q`
Expected: FAIL because multi-project queries and `/api/...` routes are not implemented yet.

- [ ] **Step 3: Implement the multi-project queries and JSON routes**

```python
class ObservabilityQueries:
    def list_projects(self, *, limit: int, offset: int) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.store.fetch_all(
                """
                SELECT p.project_id, p.project_name, p.project_root,
                       MAX(r.started_at) AS latest_run_at,
                       COUNT(r.run_id) AS run_count
                FROM projects p
                LEFT JOIN runs r ON r.project_id = p.project_id
                GROUP BY p.project_id, p.project_name, p.project_root
                ORDER BY latest_run_at DESC, p.project_name ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        ]
```

```python
if path == "/api/projects":
    return {"items": self.queries.list_projects(limit=limit, offset=offset)}

if path.startswith("/api/projects/") and path.endswith("/runs"):
    return {"items": self.queries.list_project_runs(project_id=project_id, limit=limit, offset=offset)}

if path.startswith("/api/runs/") and path.endswith("/events"):
    return {"items": self.queries.list_run_events(run_id=run_id, limit=limit, offset=offset)}
```

```python
def list_run_events(self, *, run_id: str, limit: int, offset: int) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in self.store.fetch_all(
            """
            SELECT event_id, run_id, event_index, task_id, loop_id, dispatch_id, event_kind, payload_json, created_at
            FROM events
            WHERE run_id = ?
            ORDER BY event_index ASC
            LIMIT ? OFFSET ?
            """,
            (run_id, limit, offset),
        )
    ]
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `uv run pytest tests/test_observability_backend.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/delivery_flow/observability/queries.py src/delivery_flow/observability/backend.py tests/test_observability_backend.py
git commit -m "feat: add multi-project observability api"
```

### Task 3: Add The Independent HTTP Service And Packaged Static Asset Pipeline

**Files:**
- Create: `src/delivery_flow/observability/service.py`
- Create: `scripts/build_observability_ui.py`
- Create: `src/delivery_flow/observability/web_dist/.gitkeep`
- Modify: `src/delivery_flow/observability/__init__.py`
- Modify: `pyproject.toml`
- Create: `tests/test_observability_service.py`
- Modify: `tests/test_packaging_smoke.py`

- [ ] **Step 1: Write the failing service and packaging tests**

```python
def test_service_serves_api_and_packaged_index_html(tmp_path: Path) -> None:
    db_path = tmp_path / "observability.db"
    seed_multi_project_observability_db(db_path)
    service = build_observability_service(db_path=db_path, static_root=tmp_path / "static")

    response = service.handle("GET", "/")
    api = service.handle("GET", "/api/health")

    assert response.status == 200
    assert "text/html" in response.content_type
    assert api.json == {"status": "ok"}
```

```python
def test_built_wheel_includes_packaged_observability_ui_assets(tmp_path: Path) -> None:
    wheel_path = build_repo_wheel(tmp_path)
    members = wheel_members(wheel_path)

    assert "delivery_flow/observability/web_dist/index.html" in members
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_observability_service.py tests/test_packaging_smoke.py -q`
Expected: FAIL because no service or packaged UI asset path exists yet.

- [ ] **Step 3: Implement the service, build script, and package inclusion**

```python
@dataclass(frozen=True)
class ServiceResponse:
    status: int
    content_type: str
    body: bytes
    json: dict[str, object] | None = None


class ObservabilityService:
    def __init__(self, *, app: ObservabilityApp, static_root: Path) -> None:
        self.app = app
        self.static_root = static_root

    def handle(self, method: str, path: str) -> ServiceResponse:
        if path.startswith("/api/"):
            payload = self.app.handle_json(method, path)
            return ServiceResponse(status=200, content_type="application/json", body=json.dumps(payload).encode(), json=payload)

        index_html = (self.static_root / "index.html").read_bytes()
        return ServiceResponse(status=200, content_type="text/html; charset=utf-8", body=index_html)
```

```python
def copy_dist(dist_dir: Path, package_dir: Path) -> None:
    if package_dir.exists():
        shutil.rmtree(package_dir)
    shutil.copytree(dist_dir, package_dir)
```

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/delivery_flow"]

[tool.hatch.build.targets.wheel.force-include]
"src/delivery_flow/observability/web_dist" = "delivery_flow/observability/web_dist"
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `uv run pytest tests/test_observability_service.py tests/test_packaging_smoke.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/delivery_flow/observability/service.py scripts/build_observability_ui.py src/delivery_flow/observability/web_dist/.gitkeep src/delivery_flow/observability/__init__.py pyproject.toml tests/test_observability_service.py tests/test_packaging_smoke.py
git commit -m "feat: add observability service packaging"
```

### Task 4: Build The React + Vite Observability UI

**Files:**
- Create: `frontend/observability-ui/package.json`
- Create: `frontend/observability-ui/tsconfig.json`
- Create: `frontend/observability-ui/vite.config.ts`
- Create: `frontend/observability-ui/index.html`
- Create: `frontend/observability-ui/src/main.tsx`
- Create: `frontend/observability-ui/src/App.tsx`
- Create: `frontend/observability-ui/src/api.ts`
- Create: `frontend/observability-ui/src/types.ts`
- Create: `frontend/observability-ui/src/pages/ProjectsPage.tsx`
- Create: `frontend/observability-ui/src/pages/ProjectRunsPage.tsx`
- Create: `frontend/observability-ui/src/pages/RunDetailPage.tsx`
- Create: `frontend/observability-ui/src/components/StatusBadge.tsx`
- Create: `frontend/observability-ui/src/components/KeyValueTable.tsx`
- Create: `frontend/observability-ui/src/components/EmptyState.tsx`
- Create: `frontend/observability-ui/src/styles.css`
- Create: `frontend/observability-ui/src/__tests__/api.test.ts`
- Create: `frontend/observability-ui/src/__tests__/pages.test.tsx`

- [ ] **Step 1: Write the failing frontend tests**

```tsx
it("renders project names from the api client", async () => {
  server.use(
    http.get("/api/projects", () =>
      HttpResponse.json({
        items: [{ project_id: "project-a", project_name: "project-a", project_root: "/tmp/project-a" }],
      }),
    ),
  );

  render(<App />);

  expect(await screen.findByText("project-a")).toBeInTheDocument();
});
```

```tsx
it("renders run detail sections for tasks and events", async () => {
  render(<RunDetailPage />);

  expect(await screen.findByText("Tasks")).toBeInTheDocument();
  expect(await screen.findByText("Events")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the frontend tests to verify they fail**

Run: `npm --prefix frontend/observability-ui test -- --run`
Expected: FAIL because the app, routes, and API client do not exist yet.

- [ ] **Step 3: Implement the Vite app, typed API client, and pages**

```json
{
  "name": "observability-ui",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "msw": "^2.10.5",
    "typescript": "^5.8.3",
    "vite": "^6.3.5",
    "vitest": "^3.1.2"
  }
}
```

```ts
export async function fetchProjects(limit = 20, offset = 0): Promise<ProjectSummary[]> {
  const response = await fetch(`/api/projects?limit=${limit}&offset=${offset}`);
  const payload = await response.json();
  return payload.items;
}
```

```tsx
export function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    void fetchProjects().then(setProjects);
  }, []);

  return (
    <main>
      <h1>Projects</h1>
      <ul>{projects.map((project) => <li key={project.project_id}>{project.project_name}</li>)}</ul>
    </main>
  );
}
```

- [ ] **Step 4: Run the frontend tests and build to verify they pass**

Run: `npm --prefix frontend/observability-ui test -- --run && npm --prefix frontend/observability-ui run build`
Expected: PASS, with Vite emitting a `dist/` directory.

- [ ] **Step 5: Commit**

```bash
git add frontend/observability-ui
git commit -m "feat: add observability react ui"
```

### Task 5: Wire End-To-End Smoke, Docs, And Final Verification

**Files:**
- Create: `frontend/observability-ui/playwright.config.ts`
- Create: `frontend/observability-ui/tests/e2e/observability-ui.spec.ts`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `tests/test_docs_contract.py`

- [ ] **Step 1: Write the failing docs and end-to-end smoke tests**

```python
def test_project_readmes_cover_observability_service_usage() -> None:
    readme = _read("README.md")

    _assert_mentions(readme, "observability", "global database", "react", "vite", "service")
    _assert_verification_markers(
        readme,
        success_marker="completes successfully",
        tests_pass_marker="all repository tests pass",
    )
```

```ts
test("projects to run detail smoke", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Projects")).toBeVisible();
  await page.getByText("project-a").click();
  await expect(page.getByText("Run Detail")).toBeVisible();
});
```

- [ ] **Step 2: Run the docs and e2e smoke tests to verify they fail**

Run: `uv run pytest tests/test_docs_contract.py -q && npm --prefix frontend/observability-ui run test:e2e`
Expected: FAIL because README content and Playwright setup do not exist yet.

- [ ] **Step 3: Implement the docs and Playwright smoke setup**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "^1.52.0"
  }
}
```

```tsx
// RunDetailPage
return (
  <main>
    <h1>Run Detail</h1>
    <section>
      <h2>Tasks</h2>
    </section>
    <section>
      <h2>Events</h2>
    </section>
  </main>
);
```

```md
## Observability Service

- all projects write to one global observability database
- start the backend service to inspect runs in a browser
- during frontend development, run the Vite dev server separately from the Python backend
```

- [ ] **Step 4: Run the full verification suite**

Run:

```bash
npm --prefix frontend/observability-ui test -- --run
npm --prefix frontend/observability-ui run build
uv run pytest -q
```

Expected:

- frontend unit tests PASS
- Vite build PASS
- repository pytest suite PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/observability-ui/playwright.config.ts frontend/observability-ui/tests/e2e/observability-ui.spec.ts README.md README.zh-CN.md tests/test_docs_contract.py
git commit -m "docs: add observability service usage"
```

## Self-Review

- Spec coverage:
  - global single-db path and shared helper are covered by Task 1
  - stable `event_index` ordering is covered by Task 1 and Task 2
  - multi-project REST backend is covered by Task 2
  - independent backend service and packaged static assets are covered by Task 3
  - React + Vite UI is covered by Task 4
  - docs and end-to-end smoke are covered by Task 5
- Placeholder scan:
  - no `TODO` / `TBD` placeholders remain
  - every task includes exact files, commands, and test examples
- Type consistency:
  - plan consistently uses `resolve_observability_home`, `resolve_global_observability_db_path`, `event_index`, `ObservabilityQueries`, and `ObservabilityService`

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-19-observability-service-implementation-plan.md`.

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints
