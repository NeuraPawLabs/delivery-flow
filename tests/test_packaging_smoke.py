import json
import os
import subprocess
from pathlib import Path

import delivery_flow.contracts as contracts_module


def _run_command(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def test_built_wheel_exposes_public_import_surface(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = tmp_path / "dist"
    venv_dir = tmp_path / "venv"

    _run_command(
        "uv",
        "build",
        "--wheel",
        "--out-dir",
        str(dist_dir),
        "--no-build-logs",
        "--no-create-gitignore",
        cwd=repo_root,
    )

    wheel_path = next(dist_dir.glob("delivery_flow-*.whl"))

    _run_command("uv", "venv", str(venv_dir), "--seed", cwd=repo_root)
    _run_command(
        "uv",
        "pip",
        "install",
        "--python",
        str(_venv_python(venv_dir)),
        "--no-index",
        "--link-mode=copy",
        str(wheel_path),
        cwd=repo_root,
    )

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            str(_venv_python(venv_dir)),
            "-c",
            (
                "import json, delivery_flow; "
                "from delivery_flow import CONTRACT_SCHEMA_VERSION; "
                "print(json.dumps({"
                "'all': delivery_flow.__all__, "
                "'schema_version': CONTRACT_SCHEMA_VERSION, "
                "'has_helper': hasattr(delivery_flow, 'build_normalized_review_snapshot')"
                "}))"
            ),
        ],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )

    payload = json.loads(result.stdout)

    assert payload == {
        "all": [
            "CONTRACT_SCHEMA_VERSION",
            "DeliveryArtifact",
            "RequirementArtifact",
            "ReviewArtifact",
            "RuntimeResult",
            "MainAgentLoopController",
            "run_delivery_flow",
        ],
        "schema_version": contracts_module.CONTRACT_SCHEMA_VERSION,
        "has_helper": False,
    }
