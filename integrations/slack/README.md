# Slack Agent Integration for ARP

## Purpose

This integration exposes ARP workflows inside Slack as a controlled enterprise and operator interface.

Slack users can:

- request a quote
- stage a transfer
- review policy decisions
- approve or reject out-of-policy requests
- inspect audit summaries

## Safety Boundary

The Slack Agent does not execute funds directly.

Slack messages are converted into structured ARP workflow calls.

ARP remains the deterministic authority for:

- sender policy
- recipient whitelist
- transfer limits
- approval requirements
- staged execution
- idempotency
- execution locks
- audit logging

> **AI reasons. MCP exposes tools. ARP enforces. Partner rails execute.**

## Example Commands

```
/st4bl quote KES 2000 to mum for groceries
/st4bl stage KES 2000 to mum for groceries
/st4bl approve TRANSFER_ID
/st4bl reject TRANSFER_ID
/st4bl audit TRANSFER_ID
/st4bl help
```

## Architecture

```
Slack → Slack Agent → ARP MCP Client → ARP MCP Server → Policy Engine → State Machine → Rail Adapters → Audit Ledger
```

## Current Integration Status

- Slack Agent wrapper: local integration scaffold
- Slack slash command support: implemented for local development
- ARP MCP calls: routed through adapter layer
- Real Slack deployment: requires Slack credentials
- Real payment execution: disabled by default unless explicitly connected to ARP production configuration
