#!/usr/bin/env python3
"""
Local Slack Agent demo — no real Slack credentials or payment rails required.

Simulates the /st4bl command workflow end-to-end through the ARP adapter layer,
routing every command through the central handle_st4bl_command router exactly as
the live Slack handler does.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from repository root when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.slack.arp_client import reset_stores
from integrations.slack.handlers import handle_st4bl_command


SEPARATOR = "=" * 60


def _simulate(command_text: str, user_id: str = "demo-user") -> None:
    """Simulate a /st4bl command and print the response."""
    print(f"\n{SEPARATOR}")
    print(f"  /st4bl {command_text}")
    print(SEPARATOR)
    response = handle_st4bl_command(command_text, user_id=user_id)
    print(response)
    print()


def main() -> None:
    # Reset stores so transfer IDs are deterministic from DEMO-001.
    reset_stores()

    print("St4bl / ARP Slack Agent — local demo")
    print("Slack is the channel. ARP is the enforcement layer.")
    print("AI reasons. MCP exposes tools. ARP enforces. Partner rails execute.")

    # 1. Help
    _simulate("help")

    # 2. Quote
    _simulate("quote KES 2000 to mum for groceries")

    # 3. Stage  →  creates DEMO-001
    _simulate("stage KES 2000 to mum for groceries")

    # 4. Approve DEMO-001
    _simulate("approve DEMO-001", user_id="demo-operator")

    # 5. Audit DEMO-001
    _simulate("audit DEMO-001")

    # 6. Stage a second transfer  →  creates DEMO-002
    _simulate("stage KES 500 to sis for transport")

    # 7. Reject DEMO-002
    _simulate("reject DEMO-002", user_id="demo-operator")

    # 8. Audit DEMO-002 — shows rejection, no execution
    _simulate("audit DEMO-002")

    # 9. Invalid command — should return helpful error
    _simulate("sendit all the money")

    print(f"\n{SEPARATOR}")
    print("Demo complete. No real Slack credentials or payment rails were called.")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
