import { expect, test } from "@playwright/test";

test("projects to run detail smoke", async ({ page }) => {
  await page.route("**/api/projects?limit=20&offset=0", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            project_id: "project-a",
            project_name: "project-a",
            project_root: "/tmp/project-a",
            run_count: 1,
            latest_run_at: "2026-04-19T00:00:00Z",
            latest_stop_reason: "pass"
          }
        ],
        limit: 20,
        offset: 0
      }
    });
  });

  await page.route("**/api/projects/project-a/runs?limit=20&offset=0", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            run_id: "run-1",
            project_id: "project-a",
            mode: "superpowers-backed",
            started_at: "2026-04-19T00:00:00Z",
            ended_at: null,
            stop_reason: "pass",
            owner_acceptance_required: false
          }
        ],
        limit: 20,
        offset: 0
      }
    });
  });

  await page.route("**/api/runs/run-1", async (route) => {
    await route.fulfill({
      json: {
        run_id: "run-1",
        project_id: "project-a",
        mode: "superpowers-backed",
        started_at: "2026-04-19T00:00:00Z",
        ended_at: null,
        stop_reason: "pass",
        owner_acceptance_required: false,
        task_count: 1,
        completed_task_count: 1
      }
    });
  });

  await page.route("**/api/runs/run-1/tasks?limit=50&offset=0", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            run_id: "run-1",
            task_id: "task-1",
            task_order: 1,
            title: "Task 1",
            goal: "Demo",
            current_state: "pass",
            loop_count: 1,
            dispatch_count: 1,
            latest_review_result: "pass",
            latest_dispatch_stage: "running_dev",
            total_loops: 1
          }
        ],
        limit: 50,
        offset: 0
      }
    });
  });

  await page.route("**/api/runs/run-1/events?limit=100&offset=0", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            event_id: "event-1",
            run_id: "run-1",
            event_index: 1,
            task_id: null,
            loop_id: null,
            dispatch_id: null,
            event_kind: "run_started",
            payload: {},
            payload_json: "{}",
            created_at: "2026-04-19T00:00:00Z"
          }
        ],
        limit: 100,
        offset: 0
      }
    });
  });

  await page.goto("/");
  await expect(page.getByText("Projects")).toBeVisible();
  await page.getByRole("link", { name: "project-a" }).click();
  await expect(page.getByText("Project Runs")).toBeVisible();
  await page.getByRole("link", { name: "run-1" }).click();
  await expect(page.getByText("Run Detail")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tasks" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Events" })).toBeVisible();
});
