from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_observability_ui.py <dist-dir>")
        return 1

    dist_dir = Path(sys.argv[1]).resolve()
    if not dist_dir.is_dir():
        print(f"dist directory not found: {dist_dir}")
        return 1

    target_dir = Path(__file__).resolve().parents[1] / "src" / "delivery_flow" / "observability" / "web_dist"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(dist_dir, target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
