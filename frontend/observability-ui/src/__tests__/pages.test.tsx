import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { RunDetailPage } from "../pages/RunDetailPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("pages", () => {
  it("renders project names from the api client", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          items: [{ project_id: "project-a", project_name: "project-a", project_root: "/tmp/project-a", run_count: 1, latest_run_at: null, latest_stop_reason: "pass" }],
          limit: 20,
          offset: 0
        })
      }),
    );

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("project-a")).toBeInTheDocument();
  });

  it("renders run detail sections for tasks and events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            run_id: "run-1",
            project_id: "project-a",
            mode: "superpowers-backed",
            started_at: "2026-04-19T00:00:00Z",
            stop_reason: "pass",
            task_count: 1,
            completed_task_count: 1
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            items: [],
            limit: 50,
            offset: 0
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            items: [],
            limit: 100,
            offset: 0
          })
        }),
    );

    render(
      <MemoryRouter initialEntries={["/runs/run-1"]}>
        <Routes>
          <Route path="/runs/:runId" element={<RunDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Tasks")).toBeInTheDocument();
      expect(screen.getByText("Events")).toBeInTheDocument();
    });
  });
});
