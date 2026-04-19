from __future__ import annotations

from dataclasses import dataclass, field

from delivery_flow.contracts.models import ExecutionMetadata


@dataclass
class RunTrace:
    mode: str
    stage_sequence: list[str] = field(default_factory=list)
    stage_events: list[dict[str, str]] = field(default_factory=list)
    execution_events: list[ExecutionMetadata] = field(default_factory=list)
    task_events: list[dict[str, str]] = field(default_factory=list)
    review_events: list[dict[str, object]] = field(default_factory=list)
    issue_actions: list[dict[str, str]] = field(default_factory=list)
    stop_reason: str | None = None
    final_summary: str = ""

    def record_stage_entry(self, stage: str) -> None:
        self.stage_sequence.append(stage)
        self.stage_events.append({"stage": stage, "event": "enter"})

    def record_stage_exit(self, stage: str) -> None:
        self.stage_events.append({"stage": stage, "event": "exit"})

    def record_task_event(self, *, task_id: str, event: str) -> None:
        self.task_events.append({"task_id": task_id, "event": event})

    def record_execution(self, *, stage: str, backend: str, executor_kind: str) -> None:
        self.execution_events.append(
            ExecutionMetadata(
                stage=stage,
                backend=backend,
                executor_kind=executor_kind,
            )
        )

    def execution_summary(self) -> str | None:
        if not self.execution_events:
            return None

        grouped_events: list[dict[str, object]] = []
        for event in self.execution_events:
            group = next(
                (
                    candidate
                    for candidate in grouped_events
                    if candidate["backend"] == event.backend and candidate["executor_kind"] == event.executor_kind
                ),
                None,
            )
            if group is None:
                group = {
                    "backend": event.backend,
                    "executor_kind": event.executor_kind,
                    "stages": [],
                }
                grouped_events.append(group)
            if event.stage not in group["stages"]:
                group["stages"].append(event.stage)

        return "; ".join(
            "backend={backend} executor_kind={executor_kind} stages={stages}".format(
                backend=str(group["backend"]),
                executor_kind=str(group["executor_kind"]),
                stages=",".join(str(stage) for stage in group["stages"]),
            )
            for group in grouped_events
        )

    def record_review(
        self,
        *,
        raw_result: str,
        normalized_result: str,
        blocker_identity: dict[str, str] | None,
    ) -> None:
        self.review_events.append(
            {
                "raw_result": raw_result,
                "normalized_result": normalized_result,
                "blocker_identity": blocker_identity,
            }
        )

    def record_issue_action(self, *, task_id: str, action: str, summary: str) -> None:
        self.issue_actions.append({"task_id": task_id, "action": action, "summary": summary})

    def build_terminal_summary(
        self,
        *,
        delivery_summary: str,
        verification_evidence: list[str],
        residual_risk: list[str],
        stop_reason,
        completed_task_ids: list[str] | None = None,
        open_issue_summaries: list[str] | None = None,
        owner_acceptance_required: bool = True,
        owner_decision_reason: str | None = None,
    ) -> str:
        self.stop_reason = stop_reason.value if hasattr(stop_reason, "value") else str(stop_reason)
        readable_reason = self.stop_reason.replace("_", " ")
        mode_line = f"mode={self.mode}"
        execution_summary = self.execution_summary()
        if execution_summary:
            mode_line = f"{mode_line} orchestration: {execution_summary}"
        lines = [
            mode_line,
            f"delivery: {delivery_summary}",
            "verification: "
            + (", ".join(verification_evidence) if verification_evidence else "none recorded"),
            f"residual risk: {', '.join(residual_risk) if residual_risk else 'none'}",
            "completed tasks: "
            + (", ".join(completed_task_ids) if completed_task_ids else "none"),
            "open issues: "
            + (", ".join(open_issue_summaries) if open_issue_summaries else "none"),
            f"owner acceptance required: {'yes' if owner_acceptance_required else 'no'}",
            f"stop reason: {self.stop_reason}",
            f"explanation: {readable_reason}",
        ]
        if owner_decision_reason:
            lines.append(f"owner decision: {owner_decision_reason}")
        lines.append("waiting for the owner's next instruction")
        self.final_summary = "\n".join(lines)
        return self.final_summary
