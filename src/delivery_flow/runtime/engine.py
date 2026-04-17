from __future__ import annotations

from delivery_flow.runtime.models import (
    BlockerIdentity,
    ControllerState,
    NormalizedReviewResult,
    RuntimeResult,
    StopReason,
)
from delivery_flow.trace.run_trace import RunTrace


class DeliveryFlowRuntime:
    def __init__(self, adapter: object | None, capability_detector: object | None) -> None:
        self.adapter = adapter
        self.capability_detector = capability_detector
        self.state = ControllerState.DISCUSSING_REQUIREMENT
        self.mode: str | None = None
        self._sequence = [self.state.value]
        self._last_blocker_identity: BlockerIdentity | None = None
        self._previous_blocker_identity: BlockerIdentity | None = None
        self.trace: RunTrace | None = None

    def select_mode(self) -> str:
        if self.mode is not None:
            return self.mode

        if self.capability_detector is None:
            raise RuntimeError("Capability detector is required for explicit mode selection")

        try:
            has_superpowers = self.capability_detector.has_superpowers
        except AttributeError as exc:
            raise RuntimeError("Capability detector must expose `has_superpowers`")
        else:
            has_superpowers = bool(has_superpowers)
        self.mode = "superpowers-backed" if has_superpowers else "fallback"
        return self.mode

    def normalize_review_result(self, raw_result: str) -> NormalizedReviewResult:
        normalized_map = {
            "pass": NormalizedReviewResult.PASS,
            "approved": NormalizedReviewResult.PASS,
            "blocker": NormalizedReviewResult.BLOCKER,
            "changes_requested": NormalizedReviewResult.BLOCKER,
            "needs_owner_decision": NormalizedReviewResult.NEEDS_OWNER_DECISION,
            "owner_input_required": NormalizedReviewResult.NEEDS_OWNER_DECISION,
        }

        try:
            return normalized_map[raw_result]
        except KeyError as exc:
            raise RuntimeError(f"Unknown raw review result: {raw_result}") from exc

    def derive_blocker_identity(self, review_payload: dict[str, str]) -> BlockerIdentity:
        required_fields = (
            "contract_area",
            "failure_kind",
            "expected_resolution",
        )
        missing_fields = [field for field in required_fields if not review_payload.get(field)]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise RuntimeError(
                "Required verification cannot be completed with available evidence; "
                f"missing blocker identity fields: {missing}"
            )

        return BlockerIdentity(
            contract_area=review_payload["contract_area"],
            failure_kind=review_payload["failure_kind"],
            expected_resolution=review_payload["expected_resolution"],
        )

    def _reset_run_lifecycle(self) -> None:
        self.state = ControllerState.DISCUSSING_REQUIREMENT
        self._sequence = [self.state.value]
        self._last_blocker_identity = None
        self._previous_blocker_identity = None
        self.trace = None

    def _stop(
        self,
        stop_reason: StopReason,
        latest_delivery: dict[str, object],
        review_payload: dict[str, object],
    ) -> RuntimeResult:
        self._transition_to(ControllerState.WAITING_FOR_OWNER)
        final_summary = (
            self.trace.build_terminal_summary(
                delivery_summary=str(latest_delivery.get("delivery_summary", "unavailable")),
                verification_evidence=list(latest_delivery.get("verification_evidence", [])),
                residual_risk=list(latest_delivery.get("residual_risk", [])),
                stop_reason=stop_reason,
                owner_decision_reason=review_payload.get("owner_decision_reason"),
            )
            if self.trace is not None
            else ""
        )
        return RuntimeResult(
            mode=self.mode or "",
            final_state=self.state,
            stage_sequence=list(self.trace.stage_sequence if self.trace is not None else self._sequence),
            stop_reason=stop_reason,
            final_summary=final_summary,
        )

    def _handle_review(
        self,
        review_payload: dict[str, object],
        latest_delivery: dict[str, object],
    ) -> RuntimeResult:
        normalized = self.normalize_review_result(str(review_payload["raw_result"]))
        blocker_identity: dict[str, str] | None = None
        if normalized is NormalizedReviewResult.PASS:
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_payload["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
            return self._stop(StopReason.PASS, latest_delivery, review_payload)
        if normalized is NormalizedReviewResult.NEEDS_OWNER_DECISION:
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_payload["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
            return self._stop(StopReason.NEEDS_OWNER_DECISION, latest_delivery, review_payload)

        try:
            identity = self.derive_blocker_identity(review_payload)
            blocker_identity = {
                "contract_area": identity.contract_area,
                "failure_kind": identity.failure_kind,
                "expected_resolution": identity.expected_resolution,
            }
        except RuntimeError:
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_payload["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
            return self._stop(StopReason.VERIFICATION_UNAVAILABLE, latest_delivery, review_payload)

        if self.trace is not None:
            self.trace.record_review(
                raw_result=str(review_payload["raw_result"]),
                normalized_result=normalized.value,
                blocker_identity=blocker_identity,
            )

        if identity == self._last_blocker_identity == self._previous_blocker_identity:
            return self._stop(StopReason.SAME_BLOCKER, latest_delivery, review_payload)

        self._previous_blocker_identity = self._last_blocker_identity
        self._last_blocker_identity = identity
        self._transition_to(ControllerState.RUNNING_FIX)
        fix_result = self.adapter.run_fix({"review": review_payload, "delivery": latest_delivery})
        self._transition_to(ControllerState.RUNNING_REVIEW)
        next_review = self.adapter.run_review(fix_result)
        return self._handle_review(next_review, fix_result)

    def _transition_to(self, new_state: ControllerState) -> None:
        valid = {
            ControllerState.DISCUSSING_REQUIREMENT: {ControllerState.WRITING_SPEC},
            ControllerState.WRITING_SPEC: {ControllerState.PLANNING},
            ControllerState.PLANNING: {ControllerState.RUNNING_DEV},
            ControllerState.RUNNING_DEV: {ControllerState.RUNNING_REVIEW},
            ControllerState.RUNNING_REVIEW: {ControllerState.RUNNING_FIX, ControllerState.WAITING_FOR_OWNER},
            ControllerState.RUNNING_FIX: {ControllerState.RUNNING_REVIEW},
        }
        if new_state not in valid.get(self.state, set()):
            raise RuntimeError(f"Invalid state transition: {self.state} -> {new_state}")
        previous_state = self.state
        if self.trace is not None:
            self.trace.record_stage_exit(previous_state.value)
        self.state = new_state
        self._sequence.append(new_state.value)
        if self.trace is not None:
            self.trace.record_stage_entry(new_state.value)

    def run(self, payload: dict[str, object]) -> RuntimeResult:
        if self.adapter is None:
            raise RuntimeError("Runtime adapter is required")

        self._reset_run_lifecycle()
        self.select_mode()
        self.trace = RunTrace(mode=self.mode or "")
        self.trace.record_stage_entry(self.state.value)
        self._transition_to(ControllerState.WRITING_SPEC)
        spec_result = self.adapter.discuss_and_spec(payload)
        self._transition_to(ControllerState.PLANNING)
        plan_result = self.adapter.plan(spec_result)
        self._transition_to(ControllerState.RUNNING_DEV)
        dev_result = self.adapter.run_dev(plan_result)
        self._transition_to(ControllerState.RUNNING_REVIEW)
        review_result = self.adapter.run_review(dev_result)
        return self._handle_review(review_result, dev_result)
