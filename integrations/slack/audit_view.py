"""Slack-readable audit and quote formatting helpers."""

from __future__ import annotations

from typing import Any


def format_route_quote(quote: dict[str, Any]) -> str:
    """Format a routing quote for Slack (no secrets)."""
    return "\n".join(
        [
            "*Route Quote*",
            f"Rail: `{quote.get('rail_name')}`",
            f"Source: {quote.get('source_amount')} {quote.get('source_asset')}",
            f"Target: {quote.get('target_amount')} {quote.get('target_currency')}",
            f"FX rate: {quote.get('conversion_rate')}",
            f"Est. net received: {quote.get('estimated_net_received')} {quote.get('target_currency')}",
            f"Fees: {quote.get('mpesa_withdrawal_fee', 0):.2f}",
            f"Note: {quote.get('sandbox_rails_note', 'Circle StableFX / EURC sandbox quotes only.')}",
        ]
    )


def format_policy_decision(policy: dict[str, Any]) -> str:
    """Format a policy decision for Slack."""
    lines = [
        "*Policy Decision*",
        f"Tier: {policy.get('tier')}",
        f"Allowed: {'yes' if policy.get('allowed') else 'no'}",
        f"Approval required: {'yes' if policy.get('requires_approval') else 'no'}",
    ]
    if policy.get("approval_reason"):
        lines.append(f"Reason: {policy['approval_reason']}")
    lines.append(f"Consent class: {policy.get('consent_class')}")
    return "\n".join(lines)


def format_audit_summary(audit: dict[str, Any]) -> str:
    """Format an audit summary for Slack without leaking sensitive data."""
    lines = [
        "*Audit Summary*",
        f"Transfer ID: `{audit.get('transfer_id')}`",
        f"State: {audit.get('current_state')}",
        f"Approval: {audit.get('approval_status')}",
        f"Events: {audit.get('event_count', 0)}",
    ]
    for event in audit.get("events", [])[-5:]:
        lines.append(
            f"• {event.get('timestamp', '')} — {event.get('event')}"
        )
    return "\n".join(lines)
