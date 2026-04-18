from __future__ import annotations

from dataclasses import asdict

from delivery_flow.contracts import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    PlanTaskArtifact,
    RequirementArtifact,
    ReviewArtifact,
    RuntimeResult,
    TaskExecutionContext,
)
from delivery_flow.contracts.protocols import CapabilityDetector, ExecutionBackend
from delivery_flow.runtime.models import (
    BlockerIdentity,
    ControllerState,
    NormalizedReviewResult,
    StopReason,
)
from delivery_flow.trace.run_trace import RunTrace


class DeliveryFlowRuntime:
    def __init__(
        self,
        adapter: ExecutionBackend | None,
        capability_detector: CapabilityDetector | None,
    ) -> None:
        self.adapter = adapter
        self.capability_detector = capability_detector
        self.state = ControllerState.DISCUSSING_REQUIREMENT
        self.mode: str | None = None
        self._sequence = [self.state.value]
        self._last_blocker_identity: BlockerIdentity | None = None
        self._previous_blocker_identity: BlockerIdentity | None = None
        self._completed_task_ids: list[str] = []
        self._pending_task_id: str | None = None
        self._open_issue_summaries: list[str] = []
        self._owner_acceptance_required = True
        self.trace: RunTrace | None = None

    def _coerce_plan_task(self, payload: PlanTaskArtifact | dict[str, object], index: int) -> PlanTaskArtifact:
        if isinstance(payload, PlanTaskArtifact):
            return payload

        return PlanTaskArtifact(
            task_id=str(payload.get("task_id") or f"task-{index + 1}"),
            title=str(payload.get("title") or f"Task {index + 1}"),
            goal=str(payload.get("goal") or payload.get("title") or f"Execute task-{index + 1}"),
            verification_commands=[str(command) for command in payload.get("verification_commands", [])],
        )

    def _coerce_plan_artifact(self, payload: PlanArtifact | dict[str, object]) -> PlanArtifact:
        if isinstance(payload, PlanArtifact):
            return payload

        source = payload.get("plan_artifact")
        if isinstance(source, PlanArtifact):
            return source
        if not isinstance(source, dict):
            source = payload

        raw_tasks = source.get("tasks")
        if isinstance(raw_tasks, list) and raw_tasks:
            return PlanArtifact(
                summary=str(source.get("summary", "planned work")),
                tasks=[self._coerce_plan_task(task_payload, index) for index, task_payload in enumerate(raw_tasks)],
            )

        return PlanArtifact(
            summary=str(source.get("summary", "planned work")),
            tasks=[
                PlanTaskArtifact(
                    task_id="task-1",
                    title="Planned task",
                    goal=str(source.get("goal", source.get("summary", "Execute planned work"))),
                    verification_commands=[str(command) for command in source.get("verification_commands", [])],
                )
            ],
        )

    def _coerce_delivery_artifact(self, payload: DeliveryArtifact | dict[str, object]) -> DeliveryArtifact:
        if isinstance(payload, DeliveryArtifact):
            return payload

        return DeliveryArtifact(
            delivery_summary=str(payload.get("delivery_summary", "unavailable")),
            verification_evidence=[str(item) for item in payload.get("verification_evidence", [])],
            residual_risk=[str(item) for item in payload.get("residual_risk", [])],
        )

    def _coerce_review_artifact(self, payload: ReviewArtifact | dict[str, object]) -> ReviewArtifact:
        if isinstance(payload, ReviewArtifact):
            return payload

        return ReviewArtifact(
            raw_result=str(payload["raw_result"]),
            findings=[str(item) for item in payload.get("findings", [])],
            verification_gaps=[str(item) for item in payload.get("verification_gaps", [])],
            required_changes=[str(item) for item in payload.get("required_changes", [])],
            testing_issues=[str(item) for item in payload.get("testing_issues", [])],
            maintainability_issues=[str(item) for item in payload.get("maintainability_issues", [])],
            contract_area=str(payload.get("contract_area", "")),
            failure_kind=str(payload.get("failure_kind", "")),
            expected_resolution=str(payload.get("expected_resolution", "")),
            owner_decision_reason=(
                str(payload["owner_decision_reason"]) if payload.get("owner_decision_reason") is not None else None
            ),
        )

    def _coerce_finalization_artifact(
        self,
        payload: FinalizationArtifact | dict[str, object] | None,
        latest_delivery: DeliveryArtifact | dict[str, object],
    ) -> FinalizationArtifact:
        latest = self._coerce_delivery_artifact(latest_delivery)
        if isinstance(payload, FinalizationArtifact):
            return payload

        source = payload or {}
        return FinalizationArtifact(
            delivery_summary=str(source.get("delivery_summary", latest.delivery_summary)),
            verification_evidence=[str(item) for item in source.get("verification_evidence", latest.verification_evidence)],
            residual_risk=[str(item) for item in source.get("residual_risk", latest.residual_risk)],
            owner_acceptance_required=bool(source.get("owner_acceptance_required", True)),
            final_review_summary=str(source.get("final_review_summary", source.get("final_summary", ""))),
        )

    def _build_task_context(
        self,
        plan: PlanArtifact,
        task_index: int,
        *,
        latest_delivery: DeliveryArtifact | dict[str, object] | None = None,
        latest_review: ReviewArtifact | dict[str, object] | None = None,
    ) -> TaskExecutionContext:
        return TaskExecutionContext(
            plan=plan,
            task=plan.tasks[task_index],
            task_index=task_index,
            total_tasks=len(plan.tasks),
            latest_delivery=(
                self._coerce_delivery_artifact(latest_delivery) if latest_delivery is not None else None
            ),
            latest_review=self._coerce_review_artifact(latest_review) if latest_review is not None else None,
        )

    def _reset_task_blockers(self) -> None:
        self._last_blocker_identity = None
        self._previous_blocker_identity = None

    def _summarize_blocker(self, blocker_identity: dict[str, str]) -> str:
        return (
            f"{blocker_identity['contract_area']}: {blocker_identity['failure_kind']} -> "
            f"{blocker_identity['expected_resolution']}"
        )

    def _summarize_open_issues(
        self,
        review_payload: dict[str, object],
        blocker_identity: dict[str, str] | None = None,
    ) -> list[str]:
        summaries: list[str] = []

        for field in ("findings", "required_changes", "testing_issues", "maintainability_issues"):
            for item in review_payload.get(field, []):
                summary = str(item)
                if summary not in summaries:
                    summaries.append(summary)

        owner_reason = review_payload.get("owner_decision_reason")
        if owner_reason:
            owner_summary = str(owner_reason)
            if owner_summary not in summaries:
                summaries.append(owner_summary)

        if blocker_identity is not None and not summaries:
            summaries.append(self._summarize_blocker(blocker_identity))

        return summaries

    def _summarize_verification_unavailable_issue(self, error: RuntimeError) -> str:
        message = str(error)
        marker = "missing blocker identity fields: "
        if marker in message:
            missing_fields = message.split(marker, 1)[1]
            return f"review blocker identity incomplete: missing {missing_fields}"
        return "required verification cannot be completed with available evidence"

    def _review_requires_blocker_downgrade(self, review_payload: dict[str, object]) -> bool:
        return any(
            review_payload.get(field)
            for field in ("required_changes", "testing_issues", "maintainability_issues")
        )

    def _apply_strict_pass_blocker_defaults(self, review_payload: dict[str, object]) -> None:
        review_payload.setdefault("contract_area", "review")
        review_payload.setdefault(
            "failure_kind",
            ", ".join(
                field
                for field in ("required_changes", "testing_issues", "maintainability_issues")
                if review_payload.get(field)
            ),
        )
        review_payload.setdefault(
            "expected_resolution",
            "resolve strict pass review issues before continuing",
        )

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

    def derive_blocker_identity(self, review_payload: ReviewArtifact | dict[str, str]) -> BlockerIdentity:
        if isinstance(review_payload, ReviewArtifact):
            review_payload = {
                "contract_area": review_payload.contract_area,
                "failure_kind": review_payload.failure_kind,
                "expected_resolution": review_payload.expected_resolution,
            }

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
        self._reset_task_blockers()
        self._completed_task_ids = []
        self._pending_task_id = None
        self._open_issue_summaries = []
        self._owner_acceptance_required = True
        self.trace = None

    def _stop(
        self,
        stop_reason: StopReason,
        latest_delivery: DeliveryArtifact | FinalizationArtifact | dict[str, object],
        review_payload: ReviewArtifact | dict[str, object],
    ) -> RuntimeResult:
        delivery_payload = (
            asdict(latest_delivery)
            if isinstance(latest_delivery, (DeliveryArtifact, FinalizationArtifact))
            else latest_delivery
        )
        review_dict = asdict(review_payload) if isinstance(review_payload, ReviewArtifact) else review_payload
        self._transition_to(ControllerState.WAITING_FOR_OWNER)
        final_summary = (
            self.trace.build_terminal_summary(
                delivery_summary=str(delivery_payload.get("delivery_summary", "unavailable")),
                verification_evidence=list(delivery_payload.get("verification_evidence", [])),
                residual_risk=list(delivery_payload.get("residual_risk", [])),
                stop_reason=stop_reason,
                completed_task_ids=list(self._completed_task_ids),
                open_issue_summaries=list(self._open_issue_summaries),
                owner_acceptance_required=self._owner_acceptance_required,
                owner_decision_reason=review_dict.get("owner_decision_reason"),
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
            completed_task_ids=list(self._completed_task_ids),
            pending_task_id=self._pending_task_id,
            open_issue_summaries=list(self._open_issue_summaries),
            owner_acceptance_required=self._owner_acceptance_required,
        )

    def _handle_review(
        self,
        plan_artifact: PlanArtifact,
        task_index: int,
        review_payload: ReviewArtifact | dict[str, object],
        latest_delivery: DeliveryArtifact | dict[str, object],
    ) -> tuple[RuntimeResult | None, DeliveryArtifact | dict[str, object]]:
        review_dict = asdict(review_payload) if isinstance(review_payload, ReviewArtifact) else dict(review_payload)
        task_id = plan_artifact.tasks[task_index].task_id
        normalized = self.normalize_review_result(str(review_dict["raw_result"]))
        if normalized is NormalizedReviewResult.PASS and self._review_requires_blocker_downgrade(review_dict):
            self._apply_strict_pass_blocker_defaults(review_dict)
            normalized = NormalizedReviewResult.BLOCKER
        blocker_identity: dict[str, str] | None = None
        if normalized is NormalizedReviewResult.PASS:
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_dict["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
            return None, latest_delivery
        if normalized is NormalizedReviewResult.NEEDS_OWNER_DECISION:
            self._open_issue_summaries = self._summarize_open_issues(review_dict)
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_dict["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
                if self._open_issue_summaries:
                    self.trace.record_issue_action(
                        task_id=task_id,
                        action="owner_decision_required",
                        summary=self._open_issue_summaries[0],
                    )
            return self._stop(StopReason.NEEDS_OWNER_DECISION, latest_delivery, review_dict), latest_delivery

        try:
            identity = self.derive_blocker_identity(review_dict)
            blocker_identity = {
                "contract_area": identity.contract_area,
                "failure_kind": identity.failure_kind,
                "expected_resolution": identity.expected_resolution,
            }
        except RuntimeError as error:
            if self.trace is not None:
                self.trace.record_review(
                    raw_result=str(review_dict["raw_result"]),
                    normalized_result=normalized.value,
                    blocker_identity=None,
                )
            issue_summaries = self._summarize_open_issues(review_dict)
            if not issue_summaries:
                issue_summaries = [self._summarize_verification_unavailable_issue(error)]
            self._open_issue_summaries = issue_summaries
            if self.trace is not None:
                self.trace.record_issue_action(
                    task_id=task_id,
                    action="verification_unavailable",
                    summary=issue_summaries[0],
                )
            return self._stop(StopReason.VERIFICATION_UNAVAILABLE, latest_delivery, review_dict), latest_delivery

        issue_summary = self._summarize_blocker(blocker_identity)
        if self.trace is not None:
            self.trace.record_review(
                raw_result=str(review_dict["raw_result"]),
                normalized_result=normalized.value,
                blocker_identity=blocker_identity,
            )
            self.trace.record_issue_action(
                task_id=task_id,
                action="fix_requested",
                summary=issue_summary,
            )

        if identity == self._last_blocker_identity == self._previous_blocker_identity:
            self._open_issue_summaries = self._summarize_open_issues(review_dict, blocker_identity)
            if self.trace is not None and self._open_issue_summaries:
                self.trace.record_issue_action(
                    task_id=task_id,
                    action="owner_follow_up_required",
                    summary=self._open_issue_summaries[0],
                )
            return self._stop(StopReason.SAME_BLOCKER, latest_delivery, review_dict), latest_delivery

        self._previous_blocker_identity = self._last_blocker_identity
        self._last_blocker_identity = identity
        self._transition_to(ControllerState.RUNNING_FIX)
        fix_context = self._build_task_context(
            plan_artifact,
            task_index,
            latest_delivery=latest_delivery,
            latest_review=review_dict,
        )
        fix_result = self.adapter.run_fix(fix_context)
        self._transition_to(ControllerState.RUNNING_REVIEW)
        review_context = self._build_task_context(plan_artifact, task_index, latest_delivery=fix_result)
        next_review = self.adapter.run_review(review_context)
        return self._handle_review(plan_artifact, task_index, next_review, fix_result)

    def _transition_to(self, new_state: ControllerState) -> None:
        valid = {
            ControllerState.DISCUSSING_REQUIREMENT: {ControllerState.WRITING_SPEC},
            ControllerState.WRITING_SPEC: {ControllerState.PLANNING},
            ControllerState.PLANNING: {ControllerState.RUNNING_DEV},
            ControllerState.RUNNING_DEV: {ControllerState.RUNNING_REVIEW},
            ControllerState.RUNNING_REVIEW: {
                ControllerState.RUNNING_DEV,
                ControllerState.RUNNING_FIX,
                ControllerState.RUNNING_FINALIZE,
                ControllerState.WAITING_FOR_OWNER,
            },
            ControllerState.RUNNING_FIX: {ControllerState.RUNNING_REVIEW},
            ControllerState.RUNNING_FINALIZE: {ControllerState.WAITING_FOR_OWNER},
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

    def run(self, payload: RequirementArtifact | dict[str, object]) -> RuntimeResult:
        if self.adapter is None:
            raise RuntimeError("Runtime adapter is required")

        self._reset_run_lifecycle()
        self.select_mode()
        self.trace = RunTrace(mode=self.mode or "")
        self.trace.record_stage_entry(self.state.value)
        self._transition_to(ControllerState.WRITING_SPEC)
        requirement_payload = asdict(payload) if isinstance(payload, RequirementArtifact) else payload
        spec_result = self.adapter.discuss_and_spec(requirement_payload)
        self._transition_to(ControllerState.PLANNING)
        plan_result = self.adapter.plan(spec_result)
        plan_artifact = self._coerce_plan_artifact(plan_result)

        latest_delivery: DeliveryArtifact | dict[str, object] | None = None
        for task_index, task in enumerate(plan_artifact.tasks):
            self._reset_task_blockers()
            self._pending_task_id = task.task_id
            self._open_issue_summaries = []
            if self.trace is not None:
                self.trace.record_task_event(task_id=task.task_id, event="started")
            self._transition_to(ControllerState.RUNNING_DEV)
            dev_context = self._build_task_context(plan_artifact, task_index)
            latest_delivery = self.adapter.run_dev(dev_context)
            self._transition_to(ControllerState.RUNNING_REVIEW)
            review_context = self._build_task_context(plan_artifact, task_index, latest_delivery=latest_delivery)
            review_result = self.adapter.run_review(review_context)
            terminal_result, latest_delivery = self._handle_review(
                plan_artifact,
                task_index,
                review_result,
                latest_delivery,
            )
            if terminal_result is not None:
                return terminal_result
            self._completed_task_ids.append(task.task_id)
            self._pending_task_id = None
            self._open_issue_summaries = []
            if self.trace is not None:
                self.trace.record_task_event(task_id=task.task_id, event="completed")

        if latest_delivery is None:
            raise RuntimeError("Plan artifacts require at least one task")

        self._transition_to(ControllerState.RUNNING_FINALIZE)
        finalization_result = self.adapter.finalize(
            {
                "plan": asdict(plan_artifact),
                "latest_delivery": asdict(latest_delivery)
                if isinstance(latest_delivery, DeliveryArtifact)
                else latest_delivery,
            }
        )
        finalization_artifact = self._coerce_finalization_artifact(finalization_result, latest_delivery)
        self._owner_acceptance_required = finalization_artifact.owner_acceptance_required
        return self._stop(StopReason.PASS, finalization_artifact, {"raw_result": "approved"})
