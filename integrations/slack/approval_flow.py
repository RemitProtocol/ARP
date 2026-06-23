"""Slack approval flow helpers for out-of-policy staged transfers."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from integrations.slack import arp_client


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_approval_request(staged_transfer: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic approval request for a staged transfer."""
    transfer_id = staged_transfer["transfer_id"]
    policy = staged_transfer.get("policy", {})
    request = {
        "transfer_id": transfer_id,
        "approval_required": policy.get("requires_approval", False),
        "approval_reason": policy.get("approval_reason"),
        "status": "pending",
        "created_at": _now_iso(),
        "channel_hint": "SLACK_APPROVAL_CHANNEL",
    }
    return request


def format_approval_message(staged_transfer: dict[str, Any]) -> str:
    """Format a Slack-readable approval request message."""
    intent = staged_transfer.get("intent", {})
    quote = staged_transfer.get("quote", {})
    policy = staged_transfer.get("policy", {})
    lines = [
        "*ARP Approval Required*",
        f"Transfer ID: `{staged_transfer.get('transfer_id')}`",
        f"Recipient: {intent.get('recipient_alias', intent.get('recipient_id'))}",
        f"Amount: {intent.get('target_amount')} {intent.get('target_currency')}",
        f"Rail: {quote.get('rail_name')}",
        f"Est. fees: {quote.get('mpesa_withdrawal_fee', 0):.2f} {intent.get('target_currency')}",
        f"Est. net received: {quote.get('estimated_net_received', 0):.2f} {intent.get('target_currency')}",
        f"Reason: {policy.get('approval_reason') or 'Policy threshold exceeded'}",
        f"Status: {staged_transfer.get('approval_status', 'pending')}",
        "",
        "Slack does not move money. Approve via `/st4bl approve TRANSFER_ID`.",
    ]
    return "\n".join(lines)


def approve_transfer(transfer_id: str, approver_id: str) -> dict[str, Any]:
    """Record operator approval and issue an approval token for ARP execution."""
    staged = arp_client.get_staged_transfer(transfer_id)
    if not staged:
        return {"status": "NOT_FOUND", "transfer_id": transfer_id}
    if staged.get("state") == "REJECTED":
        return {"status": "REJECTED", "transfer_id": transfer_id, "reason": "Already rejected."}

    token = secrets.token_hex(16)
    arp_client.register_approval_token(transfer_id, token)
    staged["approval_status"] = "approved"
    staged["approved_by"] = approver_id
    staged["approved_at"] = _now_iso()
    arp_client.record_audit_event(
        "approval_granted",
        transfer_id,
        {"approver_id": approver_id},
    )
    return {
        "status": "APPROVED",
        "transfer_id": transfer_id,
        "approver_id": approver_id,
        "approval_token": token,
    }


def reject_transfer(transfer_id: str, approver_id: str) -> dict[str, Any]:
    """Reject a staged transfer; no funds move."""
    return arp_client.mark_rejected(transfer_id, approver_id)
