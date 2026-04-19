import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchProjects } from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("fetches projects from the backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          items: [{ project_id: "project-a", project_name: "project-a", project_root: "/tmp/project-a" }],
          limit: 20,
          offset: 0
        })
      }),
    );

    const result = await fetchProjects();

    expect(result.items[0].project_name).toBe("project-a");
  });
});
