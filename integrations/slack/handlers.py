"""Slash command handlers for the St4bl / ARP Slack Agent."""

from __future__ import annotations

from integrations.slack import approval_flow, arp_client, audit_view


def _usage_error() -> str:
    return (
        "Could not parse command. Example:\n"
        "`/st4bl quote KES 2000 to mum for groceries`"
    )


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
    if not args.strip():
        return _usage_error()
    intent = arp_client.discover_intent(args)
    policy = arp_client.check_policy(intent)
    quote = arp_client.get_quote(intent)
    parts = [
        "*Quote Request*",
        audit_view.format_policy_decision(policy),
        "",
        audit_view.format_route_quote(quote),
    ]
    if policy.get("requires_approval"):
        parts.append("\n_This amount would require operator approval before staging execution._")
    return "\n".join(parts)


def handle_stage(args: str) -> str:
    if not args.strip():
        return _usage_error()
    intent = arp_client.discover_intent(args)
    policy = arp_client.check_policy(intent)
    quote = arp_client.get_quote(intent)
    staged = arp_client.stage_transfer(intent, quote)

    lines = [
        "*Transfer Staged*",
        f"Transfer ID: `{staged['transfer_id']}`",
        f"State: {staged['state']}",
        f"Approval required: {'yes' if policy.get('requires_approval') else 'no'}",
        "",
        audit_view.format_route_quote(quote),
    ]
    if policy.get("requires_approval"):
        lines.append("")
        lines.append(approval_flow.format_approval_message(staged))
        lines.append(f"\nApprove: `/st4bl approve {staged['transfer_id']}`")
    else:
        lines.append(
            "\n_No operator approval required. Execution still flows through ARP only._"
        )
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
    return "\n".join(
        [
            "*Transfer Approved & Submitted to ARP*",
            f"Transfer ID: `{transfer_id}`",
            f"ARP status: {result.get('status')}",
            f"Receipt: `{result.get('receipt_id', 'n/a')}`",
            result.get("note", ""),
            "",
            "_Slack approved the request. ARP enforced policy and recorded execution._",
        ]
    )


def handle_reject(transfer_id: str, approver_id: str = "slack-operator") -> str:
    transfer_id = transfer_id.strip()
    if not transfer_id:
        return "Usage: `/st4bl reject TRANSFER_ID`"

    result = approval_flow.reject_transfer(transfer_id, approver_id)
    return "\n".join(
        [
            "*Transfer Rejected*",
            f"Transfer ID: `{transfer_id}`",
            f"Status: {result.get('status')}",
            "No funds move.",
        ]
    )


def handle_audit(transfer_id: str) -> str:
    transfer_id = transfer_id.strip()
    if not transfer_id:
        return "Usage: `/st4bl audit TRANSFER_ID`"

    audit = arp_client.get_audit_summary(transfer_id)
    return audit_view.format_audit_summary(audit)


def dispatch_command(command_text: str, user_id: str = "slack-user") -> str:
    """
    Parse `/st4bl <subcommand> ...` and route to the appropriate handler.

    Never executes a transfer from free-text alone; approve explicitly calls ARP.
    """
    text = (command_text or "").strip()
    if not text or text.lower() == "help":
        return handle_help()

    parts = text.split(maxsplit=1)
    subcommand = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if subcommand == "quote":
        return handle_quote(args)
    if subcommand == "stage":
        return handle_stage(args)
    if subcommand == "approve":
        return handle_approve(args, approver_id=user_id)
    if subcommand == "reject":
        return handle_reject(args, approver_id=user_id)
    if subcommand == "audit":
        return handle_audit(args)

    return handle_help()
