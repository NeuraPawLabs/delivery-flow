import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchProjectRuns } from "../api";
import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import type { RunSummary } from "../types";

export function ProjectRunsPage() {
  const { projectId = "" } = useParams();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchProjectRuns(projectId)
      .then((payload) => {
        setRuns(payload.items);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, [projectId]);

  if (error) {
    return <EmptyState title="Runs unavailable" body={error} />;
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Project Runs</h1>
        <p>Project: {projectId}</p>
      </header>
      {runs.length === 0 ? (
        <EmptyState title="No runs" body="This project has not emitted any delivery-flow runs yet." />
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Mode</th>
              <th>Started</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td>
                  <Link to={`/runs/${run.run_id}`}>{run.run_id}</Link>
                </td>
                <td>{run.mode}</td>
                <td>{run.started_at}</td>
                <td>
                  <StatusBadge value={run.stop_reason} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
