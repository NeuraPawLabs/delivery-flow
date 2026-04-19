export type ProjectSummary = {
  project_id: string;
  project_name: string;
  project_root: string;
  run_count: number;
  latest_run_at: string | null;
  latest_stop_reason: string | null;
};

export type RunSummary = {
  run_id: string;
  project_id: string;
  mode: string;
  started_at: string;
  ended_at: string | null;
  stop_reason: string | null;
  owner_acceptance_required: number | boolean | null;
};

export type RunDetail = RunSummary & {
  final_state?: string | null;
  task_count?: number | null;
  completed_task_count?: number | null;
};

export type TaskSummary = {
  run_id: string;
  task_id: string;
  task_order: number;
  title: string;
  goal: string;
  current_state: string;
  loop_count: number;
  dispatch_count: number;
  latest_review_result: string | null;
  latest_dispatch_stage: string | null;
  total_loops: number;
};

export type EventRecord = {
  event_id: string;
  run_id: string;
  event_index: number;
  task_id: string | null;
  loop_id: string | null;
  dispatch_id: string | null;
  event_kind: string;
  payload: Record<string, unknown>;
  payload_json: string;
  created_at: string;
};
