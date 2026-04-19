import { Link, Route, Routes } from "react-router-dom";

import { ProjectsPage } from "./pages/ProjectsPage";
import { ProjectRunsPage } from "./pages/ProjectRunsPage";
import { RunDetailPage } from "./pages/RunDetailPage";

export function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand">
          delivery-flow
        </Link>
        <p>Observability</p>
      </aside>
      <div className="content">
        <Routes>
          <Route path="/" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectRunsPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
        </Routes>
      </div>
    </div>
  );
}
