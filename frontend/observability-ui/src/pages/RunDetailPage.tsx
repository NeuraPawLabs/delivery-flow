import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { fetchRun, fetchRunEvents, fetchRunTasks } from "../api";
import { EmptyState } from "../components/EmptyState";
import { KeyValueTable } from "../components/KeyValueTable";
import { StatusBadge } from "../components/StatusBadge";
import type { EventRecord, RunDetail, TaskSummary } from "../types";

export function RunDetailPage() {
  const { runId = "" } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchRun(runId), fetchRunTasks(runId), fetchRunEvents(runId)])
      .then(([runDetail, taskPayload, eventPayload]) => {
        setRun(runDetail);
        setTasks(taskPayload.items);
        setEvents(eventPayload.items);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, [runId]);

  if (error) {
    return <EmptyState title="Run unavailable" body={error} />;
  }

  if (run === null) {
    return <EmptyState title="Loading run" body="Fetching run detail..." />;
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Run Detail</h1>
        <StatusBadge value={run.stop_reason} />
      </header>

      <section className="panel">
        <h2>Summary</h2>
        <KeyValueTable
          entries={[
            { label: "Run ID", value: run.run_id },
            { label: "Project ID", value: run.project_id },
            { label: "Mode", value: run.mode },
            { label: "Started", value: run.started_at },
            { label: "Task Count", value: run.task_count ?? 0 },
            { label: "Completed Tasks", value: run.completed_task_count ?? 0 }
          ]}
        />
      </section>

      <section className="panel">
        <h2>Tasks</h2>
        {tasks.length === 0 ? (
          <EmptyState title="No tasks" body="No task rows are available for this run." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Task</th>
                <th>State</th>
                <th>Loops</th>
                <th>Dispatches</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.task_id}>
                  <td>{task.title}</td>
                  <td>
                    <StatusBadge value={task.current_state} />
                  </td>
                  <td>{task.total_loops}</td>
                  <td>{task.dispatch_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h2>Events</h2>
        {events.length === 0 ? (
          <EmptyState title="No events" body="No event rows are available for this run." />
        ) : (
          <ol className="event-list">
            {events.map((event) => (
              <li key={event.event_id}>
                <strong>{event.event_index}.</strong> {event.event_kind}
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
