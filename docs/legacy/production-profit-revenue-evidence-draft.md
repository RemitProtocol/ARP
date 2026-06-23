> **Historical draft / illustrative evidence — not current Circle production claim.**
>
> This document was retained for hackathon submission context. Revenue ledger entries referencing `Circle_EURC` are **illustrative** and do **not** represent verified production EURC volume or Circle settlement. See the [Current Integration Status](../../README.md#current-integration-status) in the README for accurate rail status.

# Agent Remittance Protocol (ARP) — Production Profit & Revenue Evidence (Draft)

This document outlines illustrative net margins, operational expenses (OpEx), and revenue modeling for the *Build with Gemini XPRIZE* judging committee during a closed-beta testing window. **Figures are draft/illustrative unless independently verified against live fiat rails (Wise / IntaSend).**

---

## 1. Executive Financial Summary (Month 1 Cohort — Illustrative)

| Metric | Value (EUR) | Accounting Category | Operational Source |
| :--- | :--- | :--- | :--- |
| **Gross Transaction Volume (GTV)** | €1,200.00 | Ecosystem Liquidity | 8 Settled Cohort Transfers (EUR → KES Corridor) |
| **Gross Revenue Captured** | €12.00 | Protocol Inflow | 1.0% Dynamic Currency Conversion (FX) Spread |
| **Total Cost of Goods Sold (COGS)** | €0.14 | Infrastructure Outflow | Serverless Compute & LLM API Token Consumption |
| **Net Operational Profit** | €11.86 | Net Retained Earnings | Illustrative margin from configured fiat rails |
| **Protocol Gross Margin** | **98.8%** | Efficiency Index | Software-native routing advantage |

---

## 2. Granular Variable Cost of Goods Sold (COGS) Breakdown

St4bl maintains an exceptionally lean operational footprint by running a serverless, zero-custody routing architecture over public rails, keeping baseline transaction friction extremely low.

### A. AI Inference Expenses (LLM API Stack)
* **Model Selection:** Gemini 3.5 Flash and qwen3.5-flash (optimized for JSON-mode structural output payloads).
* **Average Tokens Per Session:** 1,200 Input Tokens / 450 Output Tokens (Includes text-to-intent parsing, multi-rail MCP tool execution, and guardrail validation checks).
* **True Cost Per Session:** ~€0.002 EUR per finished transfer routing lifecycle.
* **Month 1 Cohort Subtotal (8 Volume Cycles):** **€0.016 EUR**

> Qwen does not execute funds. ARP enforces policy and execution.

### B. Serverless Execution & Backend Infrastructure (Google Cloud Platform)
* **Cloud Run Allocation:** Configured to scale down to absolute zero when idle. Captures computational processing time exclusively during active Webhook routing frames.
* **Secret Manager & Firestore IO Hooks:** Minimized state transactions using aggressive local key caching models.
* **Month 1 Cohort Subtotal:** **€0.120 EUR**

---

## 3. Revenue Inflow Ledger (JSONL — Illustrative / Historical Draft)

The following matching blocks connect automated database logging to illustrative cash inflows. Entries with `settled_rail: "Circle_EURC"` reflect **draft sandbox-era labeling**, not verified production Circle EURC settlement.

```jsonl
{"event_id":"REV-001","timestamp":"2026-05-19T08:12:11Z","base_volume_eur":150.00,"fx_spread_captured_eur":1.50,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
{"event_id":"REV-002","timestamp":"2026-05-20T14:45:02Z","base_volume_eur":150.00,"fx_spread_captured_eur":1.50,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
{"event_id":"REV-003","timestamp":"2026-05-22T11:01:59Z","base_volume_eur":150.00,"fx_spread_captured_eur":1.50,"settled_rail":"Wise_Fiat"}
{"event_id":"REV-004","timestamp":"2026-05-24T10:15:02Z","base_volume_eur":105.26,"fx_spread_captured_eur":1.05,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
{"event_id":"REV-005","timestamp":"2026-05-25T19:22:40Z","base_volume_eur":300.00,"fx_spread_captured_eur":3.00,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
{"event_id":"REV-006","timestamp":"2026-05-28T09:04:12Z","base_volume_eur":150.00,"fx_spread_captured_eur":1.50,"settled_rail":"IntaSend_Fiat"}
{"event_id":"REV-007","timestamp":"2026-06-01T16:33:18Z","base_volume_eur":100.00,"fx_spread_captured_eur":1.00,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
{"event_id":"REV-008","timestamp":"2026-06-03T13:11:05Z","base_volume_eur":94.74,"fx_spread_captured_eur":0.95,"settled_rail":"Circle_EURC_Sandbox_Illustrative"}
```
