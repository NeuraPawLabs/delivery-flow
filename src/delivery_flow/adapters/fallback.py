from __future__ import annotations


class FallbackAdapter:
    def __init__(self, provider: object) -> None:
        self.provider = provider

    def discuss_and_spec(self, payload: object) -> object:
        return self.provider.discuss_and_spec(payload)

    def plan(self, payload: object) -> object:
        return self.provider.plan(payload)

    def run_dev(self, payload: object) -> object:
        return self.provider.run_dev(payload)

    def run_review(self, payload: object) -> object:
        return self.provider.run_review(payload)

    def run_fix(self, payload: object) -> object:
        return self.provider.run_fix(payload)

    def finalize(self, payload: object) -> object:
        return self.provider.finalize(payload)
