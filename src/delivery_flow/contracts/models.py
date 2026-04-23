from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from delivery_flow.runtime.models import ControllerState, StopReason

CONTRACT_SCHEMA_VERSION = "1.0"
PASS_REVIEW_RESULTS = frozenset({"approved", "pass"})
BLOCKER_REVIEW_RESULTS = frozenset({"changes_requested", "blocker"})
OWNER_DECISION_REVIEW_RESULTS = frozenset({"owner_input_required", "needs_owner_decision"})
KNOWN_REVIEW_RESULTS = PASS_REVIEW_RESULTS | BLOCKER_REVIEW_RESULTS | OWNER_DECISION_REVIEW_RESULTS
KNOWN_EXECUTION_STRATEGIES = frozenset({"subagent-driven", "inline", "unresolved"})


@dataclass(frozen=True)
class RequirementArtifact:
    ticket: int
    goal: str
    execution_strategy: str | None = None

    def __post_init__(self) -> None:
        if self.execution_strategy is not None and self.execution_strategy not in KNOWN_EXECUTION_STRATEGIES:
            raise ValueError(
                "Requirement artifacts require execution_strategy to be one of "
                + ", ".join(sorted(KNOWN_EXECUTION_STRATEGIES))
            )


@dataclass(frozen=True)
class ExecutionMetadata:
    backend: str
    executor_kind: str
    stage: str

    def __post_init__(self) -> None:
        if not all((self.backend, self.executor_kind, self.stage)):
            raise ValueError("Execution metadata must be complete")


@dataclass(frozen=True)
class PlanTaskArtifact:
    task_id: str
    title: str
    goal: str
    verification_commands: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("Plan tasks require a non-empty task_id")


@dataclass(frozen=True)
class PlanArtifact:
    summary: str
    tasks: list[PlanTaskArtifact]
    schema_version: ClassVar[str] = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.tasks:
            raise ValueError("Plan artifacts require at least one task")


@dataclass
class DeliveryArtifact:
    delivery_summary: str
    verification_evidence: list[str] = field(default_factory=list)
    residual_risk: list[str] = field(default_factory=list)
    execution_metadata: ExecutionMetadata | None = None
    schema_version: ClassVar[str] = CONTRACT_SCHEMA_VERSION


@dataclass(frozen=True)
class TaskExecutionContext:
    plan: PlanArtifact
    task: PlanTaskArtifact
    task_index: int
    total_tasks: int
    latest_delivery: DeliveryArtifact | None = None
    latest_review: ReviewArtifact | None = None
    owner_response: str | None = None


@dataclass
class ReviewArtifact:
    raw_result: str
    findings: list[str] = field(default_factory=list)
    verification_gaps: list[str] = field(default_factory=list)
    required_changes: list[str] = field(default_factory=list)
    testing_issues: list[str] = field(default_factory=list)
    maintainability_issues: list[str] = field(default_factory=list)
    execution_metadata: ExecutionMetadata | None = None
    contract_area: str = ""
    failure_kind: str = ""
    expected_resolution: str = ""
    owner_decision_reason: str | None = None
    schema_version: ClassVar[str] = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.raw_result not in KNOWN_REVIEW_RESULTS:
            raise ValueError(f"Unknown raw review result: {self.raw_result}")

        if self.raw_result in BLOCKER_REVIEW_RESULTS:
            blocker_identity = (
                self.contract_area,
                self.failure_kind,
                self.expected_resolution,
            )
            if not all(blocker_identity):
                raise ValueError("Blocker review results require blocker identity fields")

        if self.raw_result in OWNER_DECISION_REVIEW_RESULTS:
            if not self.owner_decision_reason and not self.findings:
                raise ValueError("Owner decision review results require owner decision context")


@dataclass(frozen=True)
class BlockerIdentityPayload:
    contract_area: str
    failure_kind: str
    expected_resolution: str


@dataclass
class FinalizationArtifact:
    delivery_summary: str
    verification_evidence: list[str] = field(default_factory=list)
    residual_risk: list[str] = field(default_factory=list)
    execution_metadata: ExecutionMetadata | None = None
    owner_acceptance_required: bool = True
    final_review_summary: str = ""
    schema_version: ClassVar[str] = CONTRACT_SCHEMA_VERSION


@dataclass(frozen=True)
class ResumeContextArtifact:
    plan: PlanArtifact
    task_index: int
    latest_delivery: DeliveryArtifact | None = None
    latest_review: ReviewArtifact | None = None

    def __post_init__(self) -> None:
        if self.task_index < 0 or self.task_index >= len(self.plan.tasks):
            raise ValueError("Resume context task_index must reference an existing plan task")


@dataclass
class RuntimeResult:
    mode: str
    final_state: ControllerState
    execution_strategy: str | None = None
    stage_sequence: list[str] = field(default_factory=list)
    stop_reason: StopReason | None = None
    final_summary: str = ""
    completed_task_ids: list[str] = field(default_factory=list)
    pending_task_id: str | None = None
    open_issue_summaries: list[str] = field(default_factory=list)
    owner_acceptance_required: bool = True
    resume_context: ResumeContextArtifact | None = None
    schema_version: ClassVar[str] = CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.execution_strategy is not None and self.execution_strategy not in KNOWN_EXECUTION_STRATEGIES:
            raise ValueError(
                "Runtime results require execution_strategy to be one of "
                + ", ".join(sorted(KNOWN_EXECUTION_STRATEGIES))
            )


@dataclass(frozen=True)
class ResumeRequestArtifact:
    previous_result: RuntimeResult
    owner_response: str
    restart_current_task_from_dev: bool = False
    execution_strategy: str | None = None

    def __post_init__(self) -> None:
        if not self.owner_response.strip():
            raise ValueError("Resume requests require a non-empty owner_response")
        if self.execution_strategy is not None and self.execution_strategy not in KNOWN_EXECUTION_STRATEGIES:
            raise ValueError(
                "Resume requests require execution_strategy to be one of "
                + ", ".join(sorted(KNOWN_EXECUTION_STRATEGIES))
            )
