from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from delivery_flow.observability.config import resolve_observability_db_path
from delivery_flow.observability.service import ObservabilityService, build_observability_service


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the delivery-flow observability backend.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="TCP port to bind. Default: 8000")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=resolve_observability_db_path(),
        help="SQLite observability database path. Default: global delivery-flow observability DB.",
    )
    parser.add_argument(
        "--static-root",
        type=Path,
        default=None,
        help="Optional static asset root. Defaults to the packaged web_dist assets.",
    )
    return parser.parse_args(argv)


def _build_handler(service: ObservabilityService):
    class ObservabilityRequestHandler(BaseHTTPRequestHandler):
        def _handle(self, method: str, *, include_body: bool) -> None:
            response = service.handle(method, self.path)
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            if include_body:
                self.wfile.write(response.body)

        def do_GET(self) -> None:
            self._handle("GET", include_body=True)

        def do_HEAD(self) -> None:
            self._handle("GET", include_body=False)

        def do_POST(self) -> None:
            self._handle("POST", include_body=True)

        def do_PUT(self) -> None:
            self._handle("PUT", include_body=True)

        def do_DELETE(self) -> None:
            self._handle("DELETE", include_body=True)

        def log_message(self, format: str, *args: object) -> None:
            return

    return ObservabilityRequestHandler


def serve(*, host: str, port: int, db_path: Path, static_root: Path | None) -> None:
    service = build_observability_service(db_path=Path(db_path), static_root=static_root)
    server = ThreadingHTTPServer((host, port), _build_handler(service))
    print(f"delivery-flow observability backend listening on http://{host}:{port}")
    print(f"db_path={Path(db_path)}")
    if static_root is not None:
        print(f"static_root={Path(static_root)}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    serve(
        host=args.host,
        port=args.port,
        db_path=args.db_path,
        static_root=args.static_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
