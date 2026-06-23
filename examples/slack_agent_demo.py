#!/usr/bin/env python3
"""
Local Slack Agent demo — no real Slack credentials or payment rails required.

Simulates the /st4bl command workflow end-to-end through the ARP adapter layer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow imports from repository root when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.slack import arp_client, audit_view
from integrations.slack.handlers import (
    handle_approve,
    handle_audit,
    handle_quote,
    handle_stage,
)


def _section(title: str, payload: dict) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2, default=str))


def main() -> None:
    command_text = "KES 2000 to mum for groceries"

    print("St4bl / ARP Slack Agent — local demo")
    print("Slack is the channel. ARP is the enforcement layer.")
    print("AI reasons. MCP exposes tools. ARP enforces. Partner rails execute.")

    # /st4bl quote
    print("\n--- /st4bl quote KES 2000 to mum for groceries ---")
    print(handle_quote(command_text))

    intent = arp_client.discover_intent(command_text)
    policy = arp_client.check_policy(intent)
    quote = arp_client.get_quote(intent)
    _section("Parsed intent", intent)
    _section("Policy decision", policy)
    _section("Selected mock rail / quote", quote)

    # /st4bl stage
    print("\n--- /st4bl stage KES 2000 to mum for groceries ---")
    print(handle_stage(command_text))
    staged = arp_client.stage_transfer(intent, quote)
    transfer_id = staged["transfer_id"]
    print(f"\nStaged transfer ID: {transfer_id}")

    # /st4bl approve
    print(f"\n--- /st4bl approve {transfer_id} ---")
    print(handle_approve(transfer_id, approver_id="demo-operator"))

    # /st4bl audit
    print(f"\n--- /st4bl audit {transfer_id} ---")
    audit = arp_client.get_audit_summary(transfer_id)
    print(handle_audit(transfer_id))
    _section("Audit summary", audit)

    print("\nDemo complete. No real Slack credentials or payment rails were called.")


if __name__ == "__main__":
    main()
