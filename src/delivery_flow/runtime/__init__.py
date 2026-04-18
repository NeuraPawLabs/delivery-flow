from delivery_flow.runtime.models import (
    BlockerIdentity,
    ControllerState,
    NormalizedReviewResult,
    StopReason,
)

__all__ = [
    "BlockerIdentity",
    "ControllerState",
    "DeliveryFlowRuntime",
    "NormalizedReviewResult",
    "RuntimeResult",
    "StopReason",
]


def __getattr__(name: str):
    if name == "DeliveryFlowRuntime":
        from delivery_flow.runtime.engine import DeliveryFlowRuntime

        return DeliveryFlowRuntime
    if name == "RuntimeResult":
        from delivery_flow.contracts import RuntimeResult

        return RuntimeResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
