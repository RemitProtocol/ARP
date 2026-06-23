> **Historical draft / illustrative evidence — not current Circle production claim.**
>
> This document was retained for hackathon submission context. It does **not** represent verified live Circle EURC / StableFX production settlement. See the [Current Integration Status](../../README.md#current-integration-status) in the README for accurate rail status.

# Agent Remittance Protocol (ARP) — Production Execution Evidence (Draft)

This document provides architectural and runtime context for the *Build with Gemini XPRIZE* evaluation committee. It describes the reference implementation's design and demo flows. **Circle StableFX / EURC integration is sandbox-only for EUR→EURC quote testing; production execution is a planned grant milestone.**

---

## 1. Integration Matrix (Revised Status)

| Component / Rail | Environment | Interface Protocol | Core Operational Responsibility | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Google Cloud Run** | Production | Serverless Containers | Hosts the core ARP state machine & runtime hooks | ✅ Live |
| **Gemini 3.5 Flash** | Live API | Structured JSON (MCP) | Contextual intent parsing & tool invocation (reasoning only) | ✅ Live |
| **qwen3.5-flash** | Live API | Structured JSON (MCP) | Qwen Cloud reasoning runtime for intent parsing, workflow-step selection, and explanation generation (reasoning only) | ✅ Live |
| **Circle StableFX / EURC** | Sandbox | Stellar/Polygon ERC-20 | EUR→EURC quote testing; production execution planned pending grant / approval | 🧪 Sandbox |
| **IntaSend Gateway** | Live API | REST Endpoints | Last-mile mobile money disbursement (M-Pesa) | ✅ Live |
| **Wise Gateway** | Live API | REST Endpoints | Fiat corridor failover matching where configured | ✅ Live |
| **Swypt** | Partner-validated | REST / partner API | USD→USDT→M-Pesa confirmed by partner; EURC→M-Pesa in technical validation | ⚠️ Partial |

> **Model-agnostic execution:** Gemini and Qwen are reference reasoning runtimes. ARP is the deterministic execution and safety layer. Neither model executes funds.

---

## 2. Runtime Telemetry: Gemini 3.5 Flash MCP Flow (Illustrative)

Every transaction follows the strict core design principle: **"Agent proposes, human disposes, code enforces."** The log trace below shows Gemini 3.5 Flash operating as middleware to parse human language and stage the ARP pipeline. Qwen (`qwen3.5-flash`) provides an equivalent reasoning runtime for Qwen hackathon submissions.

### Steps 1 & 2: Intent Detection & Multi-Rail Quoting (`remit_discover` & `quote`)
* **Inbound Interface Request:** *"Mum needs 15,000 KES for school fees by Friday."*
* **Gemini 3.5 Flash Processing Frame:**

```json
{
  "timestamp": "2026-06-05T10:14:22.102Z",
  "engine": "Gemini-3.5-Flash-Native",
  "intent": "REMITTANCE_PULL_REQUEST",
  "extracted_payload": {
    "target_amount": 15000.00,
    "target_currency": "KES",
    "recipient_node": "M-PESA:+254712345678",
    "context_tag": "education_fees"
  },
  "mcp_tool_chain": ["remit_discover", "quote"],
  "tool_response": {
    "identity_verification": "ERC-8004 Signed Agent Card Verified",
    "active_quotes": [
      {
        "rail": "Wise_Fiat",
        "fx_rate": 141.25,
        "fee_eur": 1.50,
        "settlement": "24h"
      },
      {
        "rail": "Circle_StableFX_EURC_Sandbox",
        "fx_rate": 143.50,
        "fee_eur": 0.00,
        "settlement": "Sandbox quote only"
      }
    ]
  }
}
```
