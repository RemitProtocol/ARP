"""
ARP MCP client adapter for the Slack Agent integration.

Slack is a channel adapter. ARP remains the enforcement layer.

When ARP_MCP_ENABLED is set and a real MCP server is reachable, wire tool calls
to stage_intent, get_routing_quote, and execute_transfer on the ARP MCP server.
By default this module uses deterministic mock responses and never calls real rails.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

# In-memory mock stores (deterministic local development only).
_STAGED_TRANSFERS: dict[str, dict[str, Any]] = {}
_AUDIT_LEDGER: list[dict[str, Any]] = []
_APPROVAL_TOKENS: dict[str, str] = {}

DEFAULT_SENDER_ID = "principal-retail-123"
MOCK_FX_RATE = 132.50
POLICY_LIMIT_KES = 5000.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _transfer_id() -> str:
    return f"trf-{uuid.uuid4().hex[:12]}"


def _audit(event: str, transfer_id: str, details: dict[str, Any]) -> None:
    _AUDIT_LEDGER.append(
        {
            "timestamp": _now_iso(),
            "event": event,
            "transfer_id": transfer_id,
            "details": details,
        }
    )


def _parse_amount_currency_recipient(text: str) -> dict[str, Any]:
    """
    Parse phrases like: KES 2000 to mum for groceries
    """
    pattern = re.compile(
        r"(?P<currency>[A-Z]{3})\s+(?P<amount>\d+(?:\.\d+)?)\s+to\s+(?P<recipient>\S+)(?:\s+for\s+(?P<purpose>.+))?",
        re.IGNORECASE,
    )
    match = pattern.search(text.strip())
    if not match:
        raise ValueError(
            "Could not parse command. Expected format: KES 2000 to mum for groceries"
        )
    groups = match.groupdict()
    return {
        "target_currency": groups["currency"].upper(),
        "target_amount": float(groups["amount"]),
        "recipient_alias": groups["recipient"],
        "purpose": (groups.get("purpose") or "family_support").strip(),
        "sender_id": DEFAULT_SENDER_ID,
    }


def discover_intent(text: str) -> dict[str, Any]:
    """
    Convert natural-language Slack text into a structured remittance intent.

    Real MCP wiring:
        remit_discover / stage_intent payload construction via ARP MCP client.
    """
    parsed = _parse_amount_currency_recipient(text)
    intent_id = str(uuid.uuid4())
    intent = {
        "intent_id": intent_id,
        "sender_id": parsed["sender_id"],
        "recipient_id": f"M-PESA:{parsed['recipient_alias']}",
        "recipient_alias": parsed["recipient_alias"],
        "target_amount": parsed["target_amount"],
        "target_currency": parsed["target_currency"],
        "source_asset": "EUR",
        "purpose": parsed["purpose"],
        "discovered_at": _now_iso(),
    }
    _audit("intent_discovered", intent_id, intent)
    return intent


def check_policy(intent: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate sender policy for the intent.

    Real MCP wiring:
        Policy engine tool call on ARP MCP server.
    """
    amount = float(intent["target_amount"])
    currency = intent.get("target_currency", "KES")
    requires_approval = currency == "KES" and amount > POLICY_LIMIT_KES
    tier = "Tier-1 Retail Micro-Remittance" if amount <= 250 else "Tier-2 Retail Premium Remittance"
    decision = {
        "allowed": True,
        "tier": tier,
        "requires_approval": requires_approval,
        "approval_reason": (
            f"Amount {amount:.2f} {currency} exceeds per-transfer approval threshold "
            f"({POLICY_LIMIT_KES:.0f} KES)."
            if requires_approval
            else None
        ),
        "consent_class": "PIN" if not requires_approval else "SLACK_OPERATOR_APPROVAL",
        "checked_at": _now_iso(),
    }
    _audit("policy_checked", intent.get("intent_id", "unknown"), decision)
    return decision


def get_quote(intent: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch a routing quote for the intent.

    Real MCP wiring:
        get_routing_quote / remit_quote on ARP MCP server.
    """
    amount = float(intent["target_amount"])
    currency = intent.get("target_currency", "KES")
    source_amount = round(amount / MOCK_FX_RATE, 2) if currency == "KES" else amount
    mpesa_fee = 85.0 if amount <= 5000 else 112.0
    net_received = max(0.0, amount - mpesa_fee) if currency == "KES" else amount

    # Prefer live fiat rails where configured; Circle quotes are sandbox-only.
    selected_rail = "IntaSend" if amount <= POLICY_LIMIT_KES else "Wise"

    quote = {
        "quote_id": f"q-{uuid.uuid4().hex[:8]}",
        "intent_id": intent.get("intent_id"),
        "rail_name": selected_rail,
        "source_amount": source_amount,
        "source_asset": intent.get("source_asset", "EUR"),
        "target_amount": amount,
        "target_currency": currency,
        "conversion_rate": MOCK_FX_RATE,
        "rail_fee": 0.0,
        "mpesa_withdrawal_fee": mpesa_fee if currency == "KES" else 0.0,
        "estimated_net_received": net_received,
        "expires_at": _now_iso(),
        "sandbox_rails_note": (
            "Circle StableFX / EURC quotes available in sandbox only; "
            "not used for production execution."
        ),
    }
    _audit("quote_fetched", intent.get("intent_id", "unknown"), quote)
    return quote


def stage_transfer(intent: dict[str, Any], quote: dict[str, Any]) -> dict[str, Any]:
    """
    Stage a transfer under ARP policy without executing funds.

    Real MCP wiring:
        stage_intent on ARP MCP server; bind quote and idempotency key.
    """
    policy = check_policy(intent)
    transfer_id = _transfer_id()
    idempotency_key = str(uuid.uuid4())

    staged = {
        "transfer_id": transfer_id,
        "intent": intent,
        "quote": quote,
        "policy": policy,
        "state": "STAGED",
        "execution_lock": False,
        "idempotency_key": idempotency_key,
        "approval_status": "pending" if policy["requires_approval"] else "not_required",
        "staged_at": _now_iso(),
    }
    _STAGED_TRANSFERS[transfer_id] = staged
    _audit("transfer_staged", transfer_id, {"state": "STAGED", "approval_status": staged["approval_status"]})
    return staged


def execute_transfer(
    staged_transfer_id: str, approval_token: str | None = None
) -> dict[str, Any]:
    """
    Execute a staged transfer only when policy approval is satisfied.

    Real MCP wiring:
        execute_transfer(intent_id, human_consent_token) on ARP MCP server.

    Slack is a channel adapter. ARP remains the enforcement layer.
    """
    staged = _STAGED_TRANSFERS.get(staged_transfer_id)
    if not staged:
        return {
            "status": "REJECTED",
            "reason": "Staged transfer not found.",
            "transfer_id": staged_transfer_id,
        }

    if staged.get("state") == "REJECTED":
        return {
            "status": "REJECTED",
            "reason": "Transfer was rejected; no funds move.",
            "transfer_id": staged_transfer_id,
        }

    if staged.get("state") == "EXECUTED":
        return {
            "status": "ALREADY_EXECUTED",
            "transfer_id": staged_transfer_id,
            "receipt_id": staged.get("receipt_id"),
        }

    policy = staged.get("policy", {})
    if policy.get("requires_approval"):
        expected = _APPROVAL_TOKENS.get(staged_transfer_id)
        if not approval_token or approval_token != expected:
            return {
                "status": "REJECTED",
                "reason": "Policy approval required before execution.",
                "transfer_id": staged_transfer_id,
            }

    if os.getenv("ARP_ENABLE_REAL_EXECUTION", "").lower() not in ("1", "true", "yes"):
        # Mock-safe execution: record intent without calling partner rails.
        receipt_id = f"rec-{uuid.uuid4().hex[:12]}"
        tx_hash = hashlib.sha256(staged_transfer_id.encode()).hexdigest()
        staged["state"] = "EXECUTED"
        staged["execution_lock"] = True
        staged["receipt_id"] = receipt_id
        staged["rail_transaction_hash"] = f"0x{tx_hash}"
        staged["executed_at"] = _now_iso()
        result = {
            "status": "SUCCESS",
            "transfer_id": staged_transfer_id,
            "receipt_id": receipt_id,
            "rail_transaction_hash": staged["rail_transaction_hash"],
            "note": "Mock execution only. Partner rails were not called.",
        }
        _audit("transfer_executed", staged_transfer_id, result)
        return result

    # Real MCP execution would be wired here when ARP production configuration is enabled.
    return {
        "status": "REJECTED",
        "reason": "Real execution path not configured in this scaffold.",
        "transfer_id": staged_transfer_id,
    }


def get_staged_transfer(transfer_id: str) -> dict[str, Any] | None:
    """Return a staged transfer record if it exists."""
    return _STAGED_TRANSFERS.get(transfer_id)


def get_audit_summary(transfer_id: str) -> dict[str, Any]:
    """Return append-only audit events for a transfer."""
    events = [e for e in _AUDIT_LEDGER if e.get("transfer_id") == transfer_id]
    staged = _STAGED_TRANSFERS.get(transfer_id, {})
    return {
        "transfer_id": transfer_id,
        "current_state": staged.get("state", "UNKNOWN"),
        "approval_status": staged.get("approval_status"),
        "events": events,
        "event_count": len(events),
    }


def record_audit_event(event: str, transfer_id: str, details: dict[str, Any]) -> None:
    """Append an audit event (public helper for integration modules)."""
    _audit(event, transfer_id, details)


def register_approval_token(transfer_id: str, token: str) -> None:
    """Internal helper used by approval_flow after operator approval."""
    _APPROVAL_TOKENS[transfer_id] = token


def mark_rejected(transfer_id: str, approver_id: str, reason: str = "operator_rejected") -> dict[str, Any]:
    """Mark a staged transfer as rejected; no funds move."""
    staged = _STAGED_TRANSFERS.get(transfer_id)
    if not staged:
        return {"status": "NOT_FOUND", "transfer_id": transfer_id}
    staged["state"] = "REJECTED"
    staged["approval_status"] = "rejected"
    staged["rejected_by"] = approver_id
    staged["rejected_at"] = _now_iso()
    _audit("transfer_rejected", transfer_id, {"reason": reason, "approver_id": approver_id})
    return {"status": "REJECTED", "transfer_id": transfer_id}
