import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchProjects } from "../api";
import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import type { ProjectSummary } from "../types";

export function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchProjects()
      .then((payload) => {
        setProjects(payload.items);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, []);

  if (error) {
    return <EmptyState title="Projects unavailable" body={error} />;
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Projects</h1>
        <p>Inspect every project writing to the global delivery-flow observability database.</p>
      </header>
      {projects.length === 0 ? (
        <EmptyState title="No projects yet" body="Run delivery-flow in any project to start collecting data." />
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Root</th>
              <th>Runs</th>
              <th>Latest</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.project_id}>
                <td>
                  <Link to={`/projects/${project.project_id}`}>{project.project_name}</Link>
                </td>
                <td>{project.project_root}</td>
                <td>{project.run_count}</td>
                <td>{project.latest_run_at ?? "n/a"}</td>
                <td>
                  <StatusBadge value={project.latest_stop_reason} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
