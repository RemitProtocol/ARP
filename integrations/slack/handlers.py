"""Slash command handlers for the St4bl / ARP Slack Agent."""

from __future__ import annotations

import logging
from typing import Any

from integrations.slack import approval_flow, arp_client, audit_view

logger = logging.getLogger("arp.slack_agent.handlers")


# ---------------------------------------------------------------------------
# Usage / parse-error helper
# ---------------------------------------------------------------------------

def _usage_error() -> str:
    return "\n".join(
        [
            "I could not parse that request.",
            "",
            "Try:",
            "`/st4bl quote KES 2000 to mum for groceries`",
            "`/st4bl stage KES 2000 to mum for groceries`",
            "`/st4bl approve DEMO-001`",
            "`/st4bl reject DEMO-001`",
            "`/st4bl audit DEMO-001`",
            "`/st4bl help`",
        ]
    )


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def handle_help() -> str:
    return "\n".join(
        [
            "*St4bl / ARP Slack Agent*",
            "",
            "Supported commands:",
            "• `/st4bl quote KES 2000 to mum for groceries`",
            "• `/st4bl stage KES 2000 to mum for groceries`",
            "• `/st4bl approve TRANSFER_ID`",
            "• `/st4bl reject TRANSFER_ID`",
            "• `/st4bl audit TRANSFER_ID`",
            "• `/st4bl help`",
            "",
            "*Safety boundary*",
            "Slack does not move money directly.",
            "AI reasons. MCP exposes tools. ARP enforces. Partner rails execute.",
            "All execution flows through ARP policy, staging, and approval checks.",
        ]
    )


def handle_quote(args: str) -> str:
    """Return a Slack-readable quote matching the spec format."""
    if not args.strip():
        return _usage_error()

    try:
        intent = arp_client.discover_intent(args)
    except ValueError:
        logger.warning("Failed to parse quote args: %r", args)
        return _usage_error()

    policy = arp_client.check_policy(intent)
    quote = arp_client.get_quote(intent)

    logger.debug("Quote intent=%s policy=%s quote=%s", intent, policy, quote)

    amount = intent["target_amount"]
    currency = intent["target_currency"]
    recipient = intent.get("recipient_alias", "unknown")
    purpose = intent.get("purpose", "unspecified")
    rail = quote.get("rail_name", "unknown")
    fee = quote.get("mpesa_withdrawal_fee", 0)
    net = quote.get("estimated_net_received", amount)
    policy_note = (
        policy.get("approval_reason")
        if policy.get("requires_approval")
        else "within demo policy"
    )

    parts = [
        "*St4bl Quote*",
        "",
        f"Recipient: {recipient}",
        f"Amount requested: {currency} {amount:,.0f}",
        f"Purpose: {purpose}",
        f"Policy: {policy_note}",
        f"Best mock rail: {rail}",
        f"Estimated fee: {currency} {fee:,.0f}",
        f"Estimated net received: {currency} {net:,.0f}",
        "Status: quote only — no money moved",
        "",
        "_Safety: Slack is the channel. ARP is the enforcement layer._",
    ]
    return "\n".join(parts)


def handle_stage(args: str) -> str:
    """Stage a transfer and return a Slack-readable summary."""
    if not args.strip():
        return _usage_error()

    try:
        intent = arp_client.discover_intent(args)
    except ValueError:
        logger.warning("Failed to parse stage args: %r", args)
        return _usage_error()

    policy = arp_client.check_policy(intent)
    quote = arp_client.get_quote(intent)
    staged = arp_client.stage_transfer(intent, quote)

    logger.debug("Staged transfer=%s", staged)

    transfer_id = staged["transfer_id"]
    amount = intent["target_amount"]
    currency = intent["target_currency"]
    recipient = intent.get("recipient_alias", "unknown")
    purpose = intent.get("purpose", "unspecified")
    rail = quote.get("rail_name", "unknown")
    fee = quote.get("mpesa_withdrawal_fee", 0)
    net = quote.get("estimated_net_received", amount)
    needs_approval = policy.get("requires_approval", False)

    lines = [
        "*Transfer Staged*",
        "",
        f"Transfer ID: `{transfer_id}`",
        f"Recipient: {recipient}",
        f"Amount: {currency} {amount:,.0f}",
        f"Purpose: {purpose}",
        f"Best mock rail: {rail}",
        f"Estimated fee: {currency} {fee:,.0f}",
        f"Estimated net received: {currency} {net:,.0f}",
        f"State: {staged['state']}",
        f"Approval required: {'yes' if needs_approval else 'no'}",
    ]

    if needs_approval:
        lines.append("")
        lines.append(approval_flow.format_approval_message(staged))
        lines.append(f"\nApprove: `/st4bl approve {transfer_id}`")
        lines.append(f"Reject:  `/st4bl reject {transfer_id}`")
    else:
        lines.append("")
        lines.append(
            "_No operator approval required. Execution still flows through ARP only._"
        )
        lines.append(f"\nApprove: `/st4bl approve {transfer_id}`")

    lines.append("")
    lines.append("_Safety: Slack is the channel. ARP is the enforcement layer._")
    return "\n".join(lines)


def handle_approve(transfer_id: str, approver_id: str = "slack-operator") -> str:
    transfer_id = transfer_id.strip()
    if not transfer_id:
        return "Usage: `/st4bl approve TRANSFER_ID`"

    approval = approval_flow.approve_transfer(transfer_id, approver_id)
    if approval.get("status") != "APPROVED":
        return f"Approval failed: {approval.get('reason', approval.get('status'))}"

    result = arp_client.execute_transfer(
        transfer_id, approval_token=approval.get("approval_token")
    )

    logger.debug("Approve result=%s", result)

    return "\n".join(
        [
            "*Transfer Approved & Executed (Mock)*",
            "",
            f"Transfer ID: `{transfer_id}`",
            f"ARP status: {result.get('status')}",
            f"Receipt: `{result.get('receipt_id', 'n/a')}`",
            result.get("note", ""),
            "",
            "_No real funds moved. Slack approved the request. ARP enforced policy._",
        ]
    )


def handle_reject(transfer_id: str, approver_id: str = "slack-operator") -> str:
    transfer_id = transfer_id.strip()
    if not transfer_id:
        return "Usage: `/st4bl reject TRANSFER_ID`"

    result = approval_flow.reject_transfer(transfer_id, approver_id)

    logger.debug("Reject result=%s", result)

    return "\n".join(
        [
            "*Transfer Rejected*",
            "",
            f"Transfer ID: `{transfer_id}`",
            f"Status: {result.get('status')}",
            "No funds moved. Transfer will not be executed.",
        ]
    )


def handle_audit(transfer_id: str) -> str:
    transfer_id = transfer_id.strip()
    if not transfer_id:
        return "Usage: `/st4bl audit TRANSFER_ID`"

    audit = arp_client.get_audit_summary(transfer_id)

    logger.debug("Audit summary=%s", audit)

    return audit_view.format_audit_summary(audit)


# ---------------------------------------------------------------------------
# Central router
# ---------------------------------------------------------------------------

def handle_st4bl_command(command_text: str, user_id: str | None = None) -> str:
    """
    Parse the text after ``/st4bl`` and route to the appropriate handler.

    Slack sends only the text *after* the slash command, e.g.:
        /st4bl quote KES 2000 to mum for groceries
    arrives as:
        command_text = "quote KES 2000 to mum for groceries"

    Never executes a transfer from free-text alone; ``approve`` explicitly
    calls ARP.
    """
    effective_user = user_id or "slack-user"
    text = (command_text or "").strip()

    logger.info("[router] raw command text: %r", text)

    if not text or text.lower() == "help":
        logger.info("[router] action=help")
        return handle_help()

    parts = text.split(maxsplit=1)
    action = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    logger.info("[router] parsed action=%r  args=%r  user=%s", action, args, effective_user)

    handler_map: dict[str, Any] = {
        "quote": lambda: handle_quote(args),
        "stage": lambda: handle_stage(args),
        "approve": lambda: handle_approve(args, approver_id=effective_user),
        "reject": lambda: handle_reject(args, approver_id=effective_user),
        "audit": lambda: handle_audit(args),
    }

    handler = handler_map.get(action)
    if handler is None:
        logger.warning("[router] unknown action=%r — returning usage error", action)
        return _usage_error()

    logger.info("[router] selected handler=%s", action)
    response = handler()
    logger.debug("[router] handler response:\n%s", response)
    return response


# Backward-compatible alias used by slack_agent.py
dispatch_command = handle_st4bl_command
