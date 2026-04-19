from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from delivery_flow.observability.backend import ObservabilityApp, build_observability_app


@dataclass(frozen=True)
class ServiceResponse:
    status: int
    content_type: str
    body: bytes
    json: dict[str, object] | None = None


@dataclass(frozen=True)
class ObservabilityService:
    app: ObservabilityApp
    static_root: Path

    def handle(self, method: str, path: str) -> ServiceResponse:
        if path.startswith("/api/"):
            payload = self.app.handle_json(method, path)
            return ServiceResponse(
                status=200 if "status" not in payload or payload.get("status") == "ok" else int(payload["status"]),
                content_type="application/json",
                body=json.dumps(payload).encode("utf-8"),
                json=payload,
            )

        static_path = self.static_root / path.lstrip("/")
        if path in {"", "/"}:
            static_path = self.static_root / "index.html"

        if static_path.is_file():
            content_type = "text/html; charset=utf-8" if static_path.suffix == ".html" else "application/octet-stream"
            return ServiceResponse(status=200, content_type=content_type, body=static_path.read_bytes())

        return ServiceResponse(status=404, content_type="text/plain; charset=utf-8", body=b"not found")


def packaged_web_dist() -> Path:
    return Path(resources.files("delivery_flow.observability").joinpath("web_dist"))


def build_observability_service(
    *,
    db_path: Path,
    static_root: Path | None = None,
) -> ObservabilityService:
    return ObservabilityService(
        app=build_observability_app(db_path),
        static_root=Path(static_root) if static_root is not None else packaged_web_dist(),
    )
