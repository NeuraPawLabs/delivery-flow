from types import SimpleNamespace

import pytest

from delivery_flow.controller import run_delivery_flow


class FakeProvider:
    def __init__(self, review_result="approved"):
        self.review_result = review_result

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return {"plan_artifact": payload}

    def run_dev(self, payload):
        return {
            "delivery_summary": "implemented default path",
            "verification_evidence": ["uv run pytest"],
            "residual_risk": [],
        }

    def run_review(self, payload):
        return {"raw_result": self.review_result, "findings": [], "verification_gaps": []}

    def run_fix(self, payload):
        return {
            "delivery_summary": "fixed finding",
            "verification_evidence": ["uv run pytest"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        return {"final_summary": payload}


def test_run_delivery_flow_defaults_into_runtime_and_emits_mode_banner() -> None:
    result = run_delivery_flow(
        payload={"ticket": 89},
        provider=FakeProvider(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.mode == "superpowers-backed"
    assert result.final_summary.startswith("mode=superpowers-backed")


def test_run_delivery_flow_rejects_missing_capability_detector() -> None:
    with pytest.raises(RuntimeError, match="Capability detector is required"):
        run_delivery_flow(payload={"ticket": 89}, provider=FakeProvider(), capability_detector=None)


class FlakyDetector:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def has_superpowers(self) -> bool:
        self.calls += 1
        return self.calls == 1


def test_run_delivery_flow_freezes_mode_selection_for_runtime_and_adapter() -> None:
    result = run_delivery_flow(
        payload={"ticket": 89},
        provider=FakeProvider(),
        capability_detector=FlakyDetector(),
    )

    assert result.mode == "superpowers-backed"
    assert result.final_summary.startswith("mode=superpowers-backed")


def test_default_use_path_does_not_require_owner_to_restitch_stages() -> None:
    result = run_delivery_flow(
        payload={"ticket": 90, "goal": "default-use path"},
        provider=FakeProvider(review_result="approved"),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert "waiting for the owner's next instruction" in result.final_summary
