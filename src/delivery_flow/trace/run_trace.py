from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunTrace:
    mode: str
    stage_sequence: list[str] = field(default_factory=list)
    stage_events: list[dict[str, str]] = field(default_factory=list)
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
        lines = [
            f"mode={self.mode}",
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
