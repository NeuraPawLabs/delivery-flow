from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_root_routing_contract_keeps_plan_presence_from_demoting_delivery_flow() -> None:
    routing_doc = _read("skills/using-delivery-flow/SKILL.md")
    bootstrap_doc = _read("skills/using-delivery-flow/bootstrap-contract.md")

    assert "plan presence alone is not enough to yield" in routing_doc
    assert "plan presence alone is not enough to yield" in bootstrap_doc


def test_root_routing_contract_treats_review_fix_continuation_as_hard_signal() -> None:
    routing_doc = _read("skills/using-delivery-flow/SKILL.md")
    bootstrap_doc = _read("skills/using-delivery-flow/bootstrap-contract.md")

    assert "review/fix continuation is a strong signal" in routing_doc
    assert "review/fix continuation is a strong signal" in bootstrap_doc


def test_root_routing_contract_requires_before_response_decision() -> None:
    routing_doc = _read("skills/using-delivery-flow/SKILL.md")
    bootstrap_doc = _read("skills/using-delivery-flow/bootstrap-contract.md")

    assert "before any response" in routing_doc
    assert "before any response" in bootstrap_doc


def test_root_routing_contract_requires_new_turn_reentry_checks() -> None:
    routing_doc = _read("skills/using-delivery-flow/SKILL.md")
    bootstrap_doc = _read("skills/using-delivery-flow/bootstrap-contract.md")

    assert "new user turn" in routing_doc
    assert "new user turn" in bootstrap_doc
