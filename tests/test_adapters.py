from delivery_flow.adapters.superpowers import SuperpowersAdapter


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


def test_superpowers_adapter_exposes_runtime_action_surface() -> None:
    adapter = SuperpowersAdapter(provider=FakeProvider())

    assert callable(adapter.discuss_and_spec)
    assert callable(adapter.plan)
    assert callable(adapter.run_dev)
    assert callable(adapter.run_review)
    assert callable(adapter.run_fix)
    assert callable(adapter.finalize)
