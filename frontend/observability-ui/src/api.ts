import type { EventRecord, ProjectSummary, RunDetail, RunSummary, TaskSummary } from "./types";

type ListResponse<T> = {
  items: T[];
  limit: number;
  offset: number;
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchProjects(limit = 20, offset = 0): Promise<ListResponse<ProjectSummary>> {
  return fetchJson<ListResponse<ProjectSummary>>(`/api/projects?limit=${limit}&offset=${offset}`);
}

export async function fetchProjectRuns(projectId: string, limit = 20, offset = 0): Promise<ListResponse<RunSummary>> {
  return fetchJson<ListResponse<RunSummary>>(`/api/projects/${projectId}/runs?limit=${limit}&offset=${offset}`);
}

export async function fetchRun(runId: string): Promise<RunDetail> {
  return fetchJson<RunDetail>(`/api/runs/${runId}`);
}

export async function fetchRunTasks(runId: string, limit = 50, offset = 0): Promise<ListResponse<TaskSummary>> {
  return fetchJson<ListResponse<TaskSummary>>(`/api/runs/${runId}/tasks?limit=${limit}&offset=${offset}`);
}

export async function fetchRunEvents(runId: string, limit = 100, offset = 0): Promise<ListResponse<EventRecord>> {
  return fetchJson<ListResponse<EventRecord>>(`/api/runs/${runId}/events?limit=${limit}&offset=${offset}`);
}
