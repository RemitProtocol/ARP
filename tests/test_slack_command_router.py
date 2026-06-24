"""Tests for the /st4bl Slack command router and handlers.

Safety: no real payment rails, no real funds, no real Slack.
All tests use deterministic mock stores.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow imports from repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.slack.arp_client import reset_stores
from integrations.slack.handlers import handle_st4bl_command


@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset in-memory stores before every test for isolation."""
    reset_stores()
    yield
    reset_stores()


# ---------------------------------------------------------------------------
# help
# ---------------------------------------------------------------------------

class TestHelp:
    def test_help_returns_command_list(self):
        result = handle_st4bl_command("help")
        assert "/st4bl quote" in result
        assert "/st4bl stage" in result
        assert "/st4bl approve" in result
        assert "/st4bl reject" in result
        assert "/st4bl audit" in result
        assert "/st4bl help" in result

    def test_empty_input_returns_help(self):
        result = handle_st4bl_command("")
        assert "St4bl / ARP Slack Agent" in result


# ---------------------------------------------------------------------------
# quote
# ---------------------------------------------------------------------------

class TestQuote:
    def test_quote_parses_correctly(self):
        result = handle_st4bl_command("quote KES 2000 to mum for groceries")
        assert "mum" in result
        assert "KES" in result
        assert "2,000" in result
        assert "groceries" in result

    def test_quote_returns_mock_rail(self):
        result = handle_st4bl_command("quote KES 2000 to mum for groceries")
        assert "IntaSend / M-Pesa B2C" in result

    def test_quote_shows_fee_and_net(self):
        result = handle_st4bl_command("quote KES 2000 to mum for groceries")
        assert "Estimated fee: KES 35" in result
        assert "Estimated net received: KES 1,965" in result

    def test_quote_states_no_money_moved(self):
        result = handle_st4bl_command("quote KES 2000 to mum for groceries")
        assert "no money moved" in result

    def test_quote_includes_safety_footer(self):
        result = handle_st4bl_command("quote KES 2000 to mum for groceries")
        assert "ARP is the enforcement layer" in result

    def test_quote_no_args_returns_usage(self):
        result = handle_st4bl_command("quote")
        assert "could not parse" in result.lower()


# ---------------------------------------------------------------------------
# stage
# ---------------------------------------------------------------------------

class TestStage:
    def test_stage_creates_transfer_id(self):
        result = handle_st4bl_command("stage KES 2000 to mum for groceries")
        assert "DEMO-001" in result

    def test_stage_shows_staged_state(self):
        result = handle_st4bl_command("stage KES 2000 to mum for groceries")
        assert "STAGED" in result

    def test_stage_shows_approval_status(self):
        result = handle_st4bl_command("stage KES 2000 to mum for groceries")
        assert "Approval required:" in result

    def test_stage_increments_id(self):
        r1 = handle_st4bl_command("stage KES 1000 to bro for rent")
        r2 = handle_st4bl_command("stage KES 500 to sis for transport")
        assert "DEMO-001" in r1
        assert "DEMO-002" in r2


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------

class TestApprove:
    def test_approve_requires_staged_transfer(self):
        result = handle_st4bl_command("approve DOES-NOT-EXIST")
        assert "failed" in result.lower() or "NOT_FOUND" in result

    def test_approve_executes_staged_transfer(self):
        handle_st4bl_command("stage KES 2000 to mum for groceries")
        result = handle_st4bl_command("approve DEMO-001", user_id="operator")
        assert "Approved" in result or "SUCCESS" in result
        assert "no real funds" in result.lower() or "Mock" in result

    def test_approve_no_args_returns_usage(self):
        result = handle_st4bl_command("approve")
        assert "Usage" in result


# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------

class TestReject:
    def test_reject_prevents_execution(self):
        handle_st4bl_command("stage KES 2000 to mum for groceries")
        reject_result = handle_st4bl_command("reject DEMO-001", user_id="operator")
        assert "Rejected" in reject_result

        # Attempting approve after reject should fail
        approve_result = handle_st4bl_command("approve DEMO-001", user_id="operator")
        assert "failed" in approve_result.lower() or "REJECTED" in approve_result

    def test_reject_nonexistent_transfer(self):
        result = handle_st4bl_command("reject DOES-NOT-EXIST")
        assert "NOT_FOUND" in result or "Rejected" in result

    def test_reject_no_args_returns_usage(self):
        result = handle_st4bl_command("reject")
        assert "Usage" in result


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_returns_summary(self):
        handle_st4bl_command("stage KES 2000 to mum for groceries")
        result = handle_st4bl_command("audit DEMO-001")
        assert "DEMO-001" in result
        assert "Audit" in result

    def test_audit_shows_state_after_approve(self):
        handle_st4bl_command("stage KES 2000 to mum for groceries")
        handle_st4bl_command("approve DEMO-001", user_id="operator")
        result = handle_st4bl_command("audit DEMO-001")
        assert "EXECUTED" in result

    def test_audit_shows_state_after_reject(self):
        handle_st4bl_command("stage KES 2000 to mum for groceries")
        handle_st4bl_command("reject DEMO-001", user_id="operator")
        result = handle_st4bl_command("audit DEMO-001")
        assert "REJECTED" in result

    def test_audit_no_args_returns_usage(self):
        result = handle_st4bl_command("audit")
        assert "Usage" in result


# ---------------------------------------------------------------------------
# Invalid / unknown commands
# ---------------------------------------------------------------------------

class TestInvalidCommand:
    def test_invalid_command_returns_helpful_error(self):
        result = handle_st4bl_command("sendit all the money")
        assert "could not parse" in result.lower()
        assert "/st4bl quote" in result
        assert "/st4bl stage" in result

    def test_gibberish_returns_usage(self):
        result = handle_st4bl_command("xyzzy foo bar")
        assert "could not parse" in result.lower()
