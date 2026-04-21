from __future__ import annotations

from dataclasses import asdict

from delivery_flow.contracts import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    PlanTaskArtifact,
    ResumeContextArtifact,
    ResumeRequestArtifact,
    RequirementArtifact,
    ReviewArtifact,
    RuntimeResult,
    TaskExecutionContext,
)
from delivery_flow.contracts.models import ExecutionMetadata
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

    def _coerce_execution_metadata(self, payload: object) -> ExecutionMetadata | None:
        if payload is None:
            return None
        if isinstance(payload, ExecutionMetadata):
            return payload
        if not isinstance(payload, dict):
            raise TypeError("execution_metadata must be an ExecutionMetadata instance or dict")

        return ExecutionMetadata(
            stage=str(payload.get("stage", "")),
            backend=str(payload.get("backend", "")),
            executor_kind=str(payload.get("executor_kind", "")),
        )

    def _record_execution_metadata(self, payload: object) -> None:
        if self.trace is None:
            return

        metadata_payload: object | None
        if isinstance(payload, (DeliveryArtifact, ReviewArtifact, FinalizationArtifact)):
            metadata_payload = payload.execution_metadata
        elif isinstance(payload, dict):
            metadata_payload = payload.get("execution_metadata")
        else:
            metadata_payload = None

        metadata = self._coerce_execution_metadata(metadata_payload)
        if metadata is None:
            return
        if metadata.stage == ControllerState.RUNNING_FINALIZE.value:
            return

        self.trace.record_execution(
            stage=metadata.stage,
            backend=metadata.backend,
            executor_kind=metadata.executor_kind,
        )

    def _coerce_delivery_artifact(self, payload: DeliveryArtifact | dict[str, object]) -> DeliveryArtifact:
        if isinstance(payload, DeliveryArtifact):
            return payload

        return DeliveryArtifact(
            delivery_summary=str(payload.get("delivery_summary", "unavailable")),
            verification_evidence=[str(item) for item in payload.get("verification_evidence", [])],
            residual_risk=[str(item) for item in payload.get("residual_risk", [])],
            execution_metadata=self._coerce_execution_metadata(payload.get("execution_metadata")),
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
            execution_metadata=self._coerce_execution_metadata(payload.get("execution_metadata")),
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
            execution_metadata=self._coerce_execution_metadata(source.get("execution_metadata")),
            owner_acceptance_required=self._coerce_bool(
                source.get("owner_acceptance_required", True),
                field_name="owner_acceptance_required",
            ),
            final_review_summary=str(source.get("final_review_summary", source.get("final_summary", ""))),
        )

    def _coerce_bool(self, payload: object, *, field_name: str) -> bool:
        if isinstance(payload, bool):
            return payload
        raise TypeError(f"{field_name} must be a bool")

    def _coerce_controller_state(self, payload: ControllerState | str) -> ControllerState:
        if isinstance(payload, ControllerState):
            return payload
        return ControllerState(str(payload))

    def _coerce_stop_reason(self, payload: StopReason | str | None) -> StopReason | None:
        if payload is None or isinstance(payload, StopReason):
            return payload
        return StopReason(str(payload))

    def _coerce_resume_context(self, payload: ResumeContextArtifact | dict[str, object]) -> ResumeContextArtifact:
        if isinstance(payload, ResumeContextArtifact):
            return payload

        return ResumeContextArtifact(
            plan=self._coerce_plan_artifact(payload["plan"]),
            task_index=int(payload["task_index"]),
            latest_delivery=self._coerce_delivery_artifact(payload["latest_delivery"]),
            latest_review=self._coerce_review_artifact(payload["latest_review"]),
        )

    def _coerce_runtime_result(self, payload: RuntimeResult | dict[str, object]) -> RuntimeResult:
        if isinstance(payload, RuntimeResult):
            return payload

        resume_context_payload = payload.get("resume_context")
        return RuntimeResult(
            mode=str(payload.get("mode", "")),
            final_state=self._coerce_controller_state(payload["final_state"]),
            stage_sequence=[str(stage) for stage in payload.get("stage_sequence", [])],
            stop_reason=self._coerce_stop_reason(payload.get("stop_reason")),
            final_summary=str(payload.get("final_summary", "")),
            completed_task_ids=[str(task_id) for task_id in payload.get("completed_task_ids", [])],
            pending_task_id=(
                str(payload["pending_task_id"]) if payload.get("pending_task_id") is not None else None
            ),
            open_issue_summaries=[str(item) for item in payload.get("open_issue_summaries", [])],
            owner_acceptance_required=self._coerce_bool(
                payload.get("owner_acceptance_required", True),
                field_name="owner_acceptance_required",
            ),
            resume_context=(
                self._coerce_resume_context(resume_context_payload)
                if resume_context_payload is not None
                else None
            ),
        )

    def _coerce_resume_request(self, payload: ResumeRequestArtifact | dict[str, object]) -> ResumeRequestArtifact:
        if isinstance(payload, ResumeRequestArtifact):
            return payload

        return ResumeRequestArtifact(
            previous_result=self._coerce_runtime_result(payload["previous_result"]),
            owner_response=str(payload["owner_response"]),
            restart_current_task_from_dev=self._coerce_bool(
                payload.get("restart_current_task_from_dev", False),
                field_name="restart_current_task_from_dev",
            ),
        )

    def _build_resume_context(
        self,
        plan_artifact: PlanArtifact,
        task_index: int,
        latest_delivery: DeliveryArtifact | dict[str, object],
        latest_review: ReviewArtifact | dict[str, object],
    ) -> ResumeContextArtifact:
        return ResumeContextArtifact(
            plan=plan_artifact,
            task_index=task_index,
            latest_delivery=self._coerce_delivery_artifact(latest_delivery),
            latest_review=self._coerce_review_artifact(latest_review),
        )

    def _build_task_context(
        self,
        plan: PlanArtifact,
        task_index: int,
        *,
        latest_delivery: DeliveryArtifact | dict[str, object] | None = None,
        latest_review: ReviewArtifact | dict[str, object] | None = None,
        owner_response: str | None = None,
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
            owner_response=owner_response,
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

    def _restore_resume_lifecycle(self, previous_result: RuntimeResult) -> None:
        if previous_result.final_state is not ControllerState.WAITING_FOR_OWNER:
            raise ValueError("Resume requests require a previous result waiting for owner input")
        if previous_result.stop_reason is not StopReason.NEEDS_OWNER_DECISION:
            raise ValueError("Resume requests require previous_result.stop_reason=needs_owner_decision")
        if previous_result.mode not in {"superpowers-backed", "fallback"}:
            raise ValueError("Resume requests require previous_result.mode to be a known mode")
        if previous_result.resume_context is None:
            raise ValueError("Resume requests require previous_result.resume_context")
        if previous_result.pending_task_id is None:
            raise ValueError("Resume requests require previous_result.pending_task_id")

        self.mode = previous_result.mode
        self.state = previous_result.final_state
        self._sequence = list(previous_result.stage_sequence or [self.state.value])
        self._reset_task_blockers()
        self._completed_task_ids = list(previous_result.completed_task_ids)
        self._pending_task_id = previous_result.pending_task_id
        self._open_issue_summaries = list(previous_result.open_issue_summaries)
        self._owner_acceptance_required = previous_result.owner_acceptance_required
        self.trace = RunTrace(mode=previous_result.mode)
        self.trace.stage_sequence = list(self._sequence)
        self.trace.stage_events = [{"stage": stage, "event": "enter"} for stage in self._sequence]

    def _stop(
        self,
        stop_reason: StopReason,
        latest_delivery: DeliveryArtifact | FinalizationArtifact | dict[str, object],
        review_payload: ReviewArtifact | dict[str, object],
        *,
        resume_context: ResumeContextArtifact | None = None,
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
            resume_context=resume_context,
        )

    def _handle_review(
        self,
        plan_artifact: PlanArtifact,
        task_index: int,
        review_payload: ReviewArtifact | dict[str, object],
        latest_delivery: DeliveryArtifact | dict[str, object],
        *,
        owner_response: str | None = None,
    ) -> tuple[RuntimeResult | None, DeliveryArtifact | dict[str, object]]:
        self._record_execution_metadata(review_payload)
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
            resume_context = self._build_resume_context(plan_artifact, task_index, latest_delivery, review_dict)
            return (
                self._stop(
                    StopReason.NEEDS_OWNER_DECISION,
                    latest_delivery,
                    review_dict,
                    resume_context=resume_context,
                ),
                latest_delivery,
            )

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
            return (
                self._stop(
                    StopReason.VERIFICATION_UNAVAILABLE,
                    latest_delivery,
                    review_dict,
                ),
                latest_delivery,
            )

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
            return (
                self._stop(
                    StopReason.SAME_BLOCKER,
                    latest_delivery,
                    review_dict,
                ),
                latest_delivery,
            )

        self._previous_blocker_identity = self._last_blocker_identity
        self._last_blocker_identity = identity
        self._transition_to(ControllerState.RUNNING_FIX)
        fix_context = self._build_task_context(
            plan_artifact,
            task_index,
            latest_delivery=latest_delivery,
            latest_review=review_dict,
            owner_response=owner_response,
        )
        fix_result = self.adapter.run_fix(fix_context)
        self._record_execution_metadata(fix_result)
        self._transition_to(ControllerState.RUNNING_REVIEW)
        review_context = self._build_task_context(
            plan_artifact,
            task_index,
            latest_delivery=fix_result,
            owner_response=owner_response,
        )
        next_review = self.adapter.run_review(review_context)
        return self._handle_review(
            plan_artifact,
            task_index,
            next_review,
            fix_result,
            owner_response=owner_response,
        )

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
            ControllerState.WAITING_FOR_OWNER: {
                ControllerState.RUNNING_DEV,
                ControllerState.RUNNING_REVIEW,
            },
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

    def _finalize_current_run(
        self,
        plan_artifact: PlanArtifact,
        latest_delivery: DeliveryArtifact | dict[str, object],
    ) -> RuntimeResult:
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

    def _execute_plan_from_task(
        self,
        plan_artifact: PlanArtifact,
        start_task_index: int,
        *,
        latest_delivery: DeliveryArtifact | dict[str, object] | None = None,
        latest_review: ReviewArtifact | dict[str, object] | None = None,
        start_with_review: bool = False,
        owner_response: str | None = None,
        resumed_current_task: bool = False,
    ) -> RuntimeResult:
        if latest_delivery is None and start_with_review:
            raise ValueError("Review resume requires latest_delivery")

        for task_index in range(start_task_index, len(plan_artifact.tasks)):
            task = plan_artifact.tasks[task_index]
            current_owner_response = owner_response if task_index == start_task_index else None
            is_resumed_task = resumed_current_task and task_index == start_task_index
            self._pending_task_id = task.task_id
            self._open_issue_summaries = []
            self._reset_task_blockers()

            if self.trace is not None and not is_resumed_task:
                self.trace.record_task_event(task_id=task.task_id, event="started")

            if start_with_review and task_index == start_task_index:
                self._transition_to(ControllerState.RUNNING_REVIEW)
                review_context = self._build_task_context(
                    plan_artifact,
                    task_index,
                    latest_delivery=latest_delivery,
                    latest_review=latest_review,
                    owner_response=current_owner_response,
                )
                review_result = self.adapter.run_review(review_context)
                terminal_result, latest_delivery = self._handle_review(
                    plan_artifact,
                    task_index,
                    review_result,
                    latest_delivery,
                    owner_response=current_owner_response,
                )
            else:
                self._transition_to(ControllerState.RUNNING_DEV)
                dev_context = self._build_task_context(
                    plan_artifact,
                    task_index,
                    latest_delivery=latest_delivery if is_resumed_task else None,
                    latest_review=latest_review if is_resumed_task else None,
                    owner_response=current_owner_response,
                )
                latest_delivery = self.adapter.run_dev(dev_context)
                self._record_execution_metadata(latest_delivery)
                self._transition_to(ControllerState.RUNNING_REVIEW)
                review_context = self._build_task_context(
                    plan_artifact,
                    task_index,
                    latest_delivery=latest_delivery,
                    owner_response=current_owner_response,
                )
                review_result = self.adapter.run_review(review_context)
                terminal_result, latest_delivery = self._handle_review(
                    plan_artifact,
                    task_index,
                    review_result,
                    latest_delivery,
                    owner_response=current_owner_response,
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

        return self._finalize_current_run(plan_artifact, latest_delivery)

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
        return self._execute_plan_from_task(plan_artifact, 0)

    def resume(self, payload: ResumeRequestArtifact | dict[str, object]) -> RuntimeResult:
        if self.adapter is None:
            raise RuntimeError("Runtime adapter is required")

        request = self._coerce_resume_request(payload)
        previous_result = request.previous_result
        resume_context = previous_result.resume_context
        if resume_context is None:
            raise ValueError("Resume requests require previous_result.resume_context")

        self._restore_resume_lifecycle(previous_result)
        plan_artifact = resume_context.plan
        current_task = plan_artifact.tasks[resume_context.task_index]
        if previous_result.pending_task_id != current_task.task_id:
            raise ValueError("Resume requests require pending_task_id to match resume_context.task_index")
        if self.trace is not None:
            self.trace.record_resume(
                task_id=current_task.task_id,
                target_stage=(
                    ControllerState.RUNNING_DEV.value
                    if request.restart_current_task_from_dev
                    else ControllerState.RUNNING_REVIEW.value
                ),
                owner_response=request.owner_response,
            )

        return self._execute_plan_from_task(
            plan_artifact,
            resume_context.task_index,
            latest_delivery=resume_context.latest_delivery,
            latest_review=resume_context.latest_review,
            start_with_review=not request.restart_current_task_from_dev,
            owner_response=request.owner_response,
            resumed_current_task=True,
        )
