from delivery_flow.drivers.superpowers import SuperpowersBackedDriver


class FakeSuperpowersProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def discuss_and_spec(self, payload: object) -> dict[str, object]:
        self.calls.append(("discuss_and_spec", payload))
        return {"spec": payload}

    def plan(self, payload: object) -> dict[str, object]:
        self.calls.append(("plan", payload))
        return {"plan": payload}

    def run_dev(self, payload: object) -> dict[str, object]:
        self.calls.append(("run_dev", payload))
        return {"delivery": payload}

    def run_review(self, payload: object) -> dict[str, object]:
        self.calls.append(("run_review", payload))
        return {"raw_result": "approved", "payload": payload}

    def run_fix(self, payload: object) -> dict[str, object]:
        self.calls.append(("run_fix", payload))
        return {"fix": payload}

    def finalize(self, payload: object) -> dict[str, object]:
        self.calls.append(("finalize", payload))
        return {"final": payload}


class PreservingSuperpowersProvider(FakeSuperpowersProvider):
    def run_review(self, payload: object) -> dict[str, object]:
        self.calls.append(("run_review", payload))
        return {
            "raw_result": "approved",
            "payload": payload,
            "execution_metadata": {
                "backend": "superpowers-backed",
                "executor_kind": "subagent",
                "stage": "running_review",
            },
        }


def test_superpowers_driver_exposes_the_full_minimal_action_surface() -> None:
    driver = SuperpowersBackedDriver(provider=FakeSuperpowersProvider())

    assert callable(driver.discuss_and_spec)
    assert callable(driver.plan)
    assert callable(driver.run_dev)
    assert callable(driver.run_review)
    assert callable(driver.run_fix)
    assert callable(driver.finalize)


def test_superpowers_driver_delegates_calls_to_provider() -> None:
    provider = FakeSuperpowersProvider()
    driver = SuperpowersBackedDriver(provider=provider)

    spec = driver.discuss_and_spec({"ticket": 1})
    plan = driver.plan({"spec": "ok"})
    delivery = driver.run_dev({"task": "build"})
    review = driver.run_review({"diff": "..."})
    fix = driver.run_fix({"finding": "x"})
    final = driver.finalize({"summary": "done"})

    assert spec == {"spec": {"ticket": 1}}
    assert plan == {"plan": {"spec": "ok"}}
    assert delivery["delivery"] == {"task": "build"}
    assert review["raw_result"] == "approved"
    assert review["payload"] == {"diff": "..."}
    assert fix["fix"] == {"finding": "x"}
    assert final["final"] == {"summary": "done"}
    assert provider.calls == [
        ("discuss_and_spec", {"ticket": 1}),
        ("plan", {"spec": "ok"}),
        ("run_dev", {"task": "build"}),
        ("run_review", {"diff": "..."}),
        ("run_fix", {"finding": "x"}),
        ("finalize", {"summary": "done"}),
    ]


def test_superpowers_driver_stamps_subagent_execution_metadata_for_post_plan_stages() -> None:
    driver = SuperpowersBackedDriver(provider=FakeSuperpowersProvider())

    delivery = driver.run_dev({"task": "build"})
    review = driver.run_review({"diff": "..."})
    fix = driver.run_fix({"finding": "x"})
    final = driver.finalize({"summary": "done"})

    assert delivery["execution_metadata"] == {
        "backend": "superpowers-backed",
        "executor_kind": "subagent",
        "stage": "running_dev",
    }
    assert review["execution_metadata"] == {
        "backend": "superpowers-backed",
        "executor_kind": "subagent",
        "stage": "running_review",
    }
    assert fix["execution_metadata"] == {
        "backend": "superpowers-backed",
        "executor_kind": "subagent",
        "stage": "running_fix",
    }
    assert "execution_metadata" not in final


def test_superpowers_driver_preserves_existing_execution_metadata() -> None:
    driver = SuperpowersBackedDriver(provider=PreservingSuperpowersProvider())

    review = driver.run_review({"diff": "..."})

    assert review["execution_metadata"] == {
        "backend": "superpowers-backed",
        "executor_kind": "subagent",
        "stage": "running_review",
    }
