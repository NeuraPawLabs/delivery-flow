from dataclasses import fields

import pytest

from delivery_flow.contracts import (
    BlockerIdentityPayload,
    CONTRACT_SCHEMA_VERSION,
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
from delivery_flow.runtime.models import ControllerState, StopReason


def test_contract_models_capture_runtime_shapes() -> None:
    requirement = RequirementArtifact(ticket=101, goal="contract-models")
    plan = PlanArtifact(
        summary="task loop",
        tasks=[
            PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
        ],
    )
    context = TaskExecutionContext(plan=plan, task=plan.tasks[0], task_index=0, total_tasks=1)
    delivery = DeliveryArtifact(
        delivery_summary="implemented",
        verification_evidence=["uv run pytest"],
        residual_risk=[],
    )
    review = ReviewArtifact(raw_result="approved")
    blocker = BlockerIdentityPayload(
        contract_area="trace",
        failure_kind="missing evidence",
        expected_resolution="record trace",
    )
    finalization = FinalizationArtifact(
        delivery_summary="all tasks passed",
        verification_evidence=["uv run pytest"],
        residual_risk=[],
    )
    result = RuntimeResult(
        mode="superpowers-backed",
        final_state=ControllerState.WAITING_FOR_OWNER,
        stage_sequence=["discussing_requirement", "waiting_for_owner"],
        stop_reason=StopReason.PASS,
        final_summary="mode=superpowers-backed",
    )

    assert requirement.ticket == 101
    assert context.task.task_id == "task-1"
    assert delivery.verification_evidence == ["uv run pytest"]
    assert review.raw_result == "approved"
    assert blocker.contract_area == "trace"
    assert finalization.owner_acceptance_required is True
    assert result.stop_reason is StopReason.PASS


def test_resume_contract_models_capture_owner_follow_up_shapes() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )
    delivery = DeliveryArtifact(delivery_summary="implemented")
    review = ReviewArtifact(
        raw_result="owner_input_required",
        findings=["choose rollout order"],
        owner_decision_reason="choose rollout order",
    )
    resume_context = ResumeContextArtifact(
        plan=plan,
        task_index=0,
        latest_delivery=delivery,
        latest_review=review,
    )
    request = ResumeRequestArtifact(
        previous_result=RuntimeResult(
            mode="superpowers-backed",
            final_state=ControllerState.WAITING_FOR_OWNER,
            stop_reason=StopReason.NEEDS_OWNER_DECISION,
            pending_task_id="task-1",
            resume_context=resume_context,
        ),
        owner_response="roll out to canary first",
    )

    assert request.owner_response == "roll out to canary first"
    assert request.restart_current_task_from_dev is False
    assert request.previous_result.resume_context == resume_context


def test_resume_request_rejects_empty_owner_response() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )

    with pytest.raises(ValueError, match="owner_response"):
        ResumeRequestArtifact(
            previous_result=RuntimeResult(
                mode="superpowers-backed",
                final_state=ControllerState.WAITING_FOR_OWNER,
                stop_reason=StopReason.NEEDS_OWNER_DECISION,
                pending_task_id="task-1",
                resume_context=ResumeContextArtifact(
                    plan=plan,
                    task_index=0,
                    latest_delivery=DeliveryArtifact(delivery_summary="implemented"),
                    latest_review=ReviewArtifact(
                        raw_result="owner_input_required",
                        findings=["choose rollout order"],
                    ),
                ),
            ),
            owner_response="   ",
        )


def test_resume_context_rejects_task_index_outside_plan_range() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )

    with pytest.raises(ValueError, match="task_index"):
        ResumeContextArtifact(
            plan=plan,
            task_index=2,
            latest_delivery=DeliveryArtifact(delivery_summary="implemented"),
            latest_review=ReviewArtifact(
                raw_result="owner_input_required",
                findings=["choose rollout order"],
            ),
        )


def test_public_contracts_expose_schema_version_markers() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[
            PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
        ],
    )
    delivery = DeliveryArtifact(delivery_summary="implemented")
    finalization = FinalizationArtifact(delivery_summary="implemented")
    review = ReviewArtifact(raw_result="approved")
    result = RuntimeResult(
        mode="superpowers-backed",
        final_state=ControllerState.WAITING_FOR_OWNER,
    )

    assert CONTRACT_SCHEMA_VERSION == "1.0"
    assert plan.schema_version == CONTRACT_SCHEMA_VERSION
    assert delivery.schema_version == CONTRACT_SCHEMA_VERSION
    assert finalization.schema_version == CONTRACT_SCHEMA_VERSION
    assert review.schema_version == CONTRACT_SCHEMA_VERSION
    assert result.schema_version == CONTRACT_SCHEMA_VERSION


def test_schema_version_is_not_a_dataclass_field() -> None:
    assert "schema_version" not in {f.name for f in fields(PlanArtifact)}
    assert "schema_version" not in {f.name for f in fields(DeliveryArtifact)}
    assert "schema_version" not in {f.name for f in fields(FinalizationArtifact)}
    assert "schema_version" not in {f.name for f in fields(ReviewArtifact)}
    assert "schema_version" not in {f.name for f in fields(RuntimeResult)}


def test_schema_version_is_not_constructor_settable() -> None:
    with pytest.raises(TypeError):
        PlanArtifact(
            summary="implemented",
            tasks=[
                PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
            ],
            schema_version="2.0",  # type: ignore[call-arg]
        )

    with pytest.raises(TypeError):
        DeliveryArtifact(
            delivery_summary="implemented",
            schema_version="2.0",  # type: ignore[call-arg]
        )

    with pytest.raises(TypeError):
        FinalizationArtifact(
            delivery_summary="implemented",
            schema_version="2.0",  # type: ignore[call-arg]
        )

    with pytest.raises(TypeError):
        ReviewArtifact(
            raw_result="approved",
            schema_version="2.0",  # type: ignore[call-arg]
        )

    with pytest.raises(TypeError):
        RuntimeResult(
            mode="superpowers-backed",
            final_state=ControllerState.WAITING_FOR_OWNER,
            schema_version="2.0",  # type: ignore[call-arg]
        )


def test_contract_equality_uses_runtime_fields_only() -> None:
    left_plan = PlanArtifact(
        summary="task loop",
        tasks=[
            PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
        ],
    )
    right_plan = PlanArtifact(
        summary="task loop",
        tasks=[
            PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
        ],
    )
    left_delivery = DeliveryArtifact(
        delivery_summary="implemented",
        verification_evidence=["uv run pytest"],
        residual_risk=["none"],
    )
    right_delivery = DeliveryArtifact(
        delivery_summary="implemented",
        verification_evidence=["uv run pytest"],
        residual_risk=["none"],
    )
    left_review = ReviewArtifact(raw_result="approved")
    right_review = ReviewArtifact(raw_result="approved")
    left_finalization = FinalizationArtifact(
        delivery_summary="implemented",
        verification_evidence=["uv run pytest"],
        residual_risk=["none"],
    )
    right_finalization = FinalizationArtifact(
        delivery_summary="implemented",
        verification_evidence=["uv run pytest"],
        residual_risk=["none"],
    )
    left_result = RuntimeResult(
        mode="superpowers-backed",
        final_state=ControllerState.WAITING_FOR_OWNER,
    )
    right_result = RuntimeResult(
        mode="superpowers-backed",
        final_state=ControllerState.WAITING_FOR_OWNER,
    )

    assert left_plan == right_plan
    assert left_delivery == right_delivery
    assert left_review == right_review
    assert left_finalization == right_finalization
    assert left_result == right_result


def test_runtime_result_accepts_known_execution_strategy() -> None:
    result = RuntimeResult(
        mode="superpowers-backed",
        execution_strategy="subagent-driven",
        final_state=ControllerState.WAITING_FOR_OWNER,
    )

    assert result.execution_strategy == "subagent-driven"


def test_runtime_result_rejects_unknown_execution_strategy() -> None:
    with pytest.raises(ValueError, match="execution_strategy"):
        RuntimeResult(
            mode="superpowers-backed",
            execution_strategy="mystery",
            final_state=ControllerState.WAITING_FOR_OWNER,
        )


def test_resume_request_accepts_execution_strategy_override() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )
    request = ResumeRequestArtifact(
        previous_result=RuntimeResult(
            mode="superpowers-backed",
            execution_strategy="subagent-driven",
            final_state=ControllerState.WAITING_FOR_OWNER,
            stop_reason=StopReason.NEEDS_OWNER_DECISION,
            pending_task_id="task-1",
            resume_context=ResumeContextArtifact(
                plan=plan,
                task_index=0,
                latest_delivery=DeliveryArtifact(delivery_summary="implemented"),
                latest_review=ReviewArtifact(
                    raw_result="owner_input_required",
                    findings=["choose rollout order"],
                ),
            ),
        ),
        owner_response="continue",
        execution_strategy="inline",
    )

    assert request.execution_strategy == "inline"


def test_resume_request_rejects_unknown_execution_strategy_override() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )

    with pytest.raises(ValueError, match="execution_strategy"):
        ResumeRequestArtifact(
            previous_result=RuntimeResult(
                mode="superpowers-backed",
                execution_strategy="subagent-driven",
                final_state=ControllerState.WAITING_FOR_OWNER,
                stop_reason=StopReason.NEEDS_OWNER_DECISION,
                pending_task_id="task-1",
                resume_context=ResumeContextArtifact(
                    plan=plan,
                    task_index=0,
                    latest_delivery=DeliveryArtifact(delivery_summary="implemented"),
                    latest_review=ReviewArtifact(
                        raw_result="owner_input_required",
                        findings=["choose rollout order"],
                    ),
                ),
            ),
            owner_response="continue",
            execution_strategy="mystery",
        )


def test_plan_artifact_requires_non_empty_task_list() -> None:
    with pytest.raises(ValueError, match="at least one task"):
        PlanArtifact(summary="empty", tasks=[])


def test_plan_task_requires_stable_task_identity() -> None:
    with pytest.raises(ValueError, match="task_id"):
        PlanTaskArtifact(task_id="", title="Runtime", goal="Refactor engine")


def test_task_execution_context_tracks_plan_and_task_position() -> None:
    plan = PlanArtifact(
        summary="task loop",
        tasks=[
            PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Refactor engine"),
            PlanTaskArtifact(task_id="task-2", title="Trace", goal="Record task evidence"),
        ],
    )

    context = TaskExecutionContext(
        plan=plan,
        task=plan.tasks[0],
        task_index=0,
        total_tasks=2,
    )

    assert context.task.task_id == "task-1"
    assert context.total_tasks == 2


def test_review_artifact_rejects_unknown_raw_result() -> None:
    with pytest.raises(ValueError, match="Unknown raw review result"):
        ReviewArtifact(raw_result="shrug")


def test_review_artifact_requires_blocker_identity_for_blocker_results() -> None:
    with pytest.raises(ValueError, match="blocker identity"):
        ReviewArtifact(raw_result="changes_requested")


def test_review_artifact_requires_owner_context_for_owner_decision_results() -> None:
    with pytest.raises(ValueError, match="owner decision context"):
        ReviewArtifact(raw_result="owner_input_required")


def test_review_artifact_accepts_valid_non_pass_variants() -> None:
    blocker_review = ReviewArtifact(
        raw_result="changes_requested",
        contract_area="trace",
        failure_kind="missing evidence",
        expected_resolution="record transitions",
    )
    owner_review = ReviewArtifact(
        raw_result="owner_input_required",
        findings=["pick rollout order"],
    )

    assert blocker_review.contract_area == "trace"
    assert owner_review.findings == ["pick rollout order"]


def test_review_artifact_exposes_strict_pass_inputs() -> None:
    review = ReviewArtifact(
        raw_result="approved",
        required_changes=["rename helper"],
        testing_issues=["missing regression test"],
        maintainability_issues=["duplicate branch"],
    )

    assert review.required_changes == ["rename helper"]
    assert review.testing_issues == ["missing regression test"]
    assert review.maintainability_issues == ["duplicate branch"]


def test_finalization_artifact_defaults_to_owner_acceptance_required() -> None:
    artifact = FinalizationArtifact(
        delivery_summary="all tasks passed",
        verification_evidence=["uv run pytest"],
        residual_risk=[],
    )

    assert artifact.owner_acceptance_required is True
