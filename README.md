# Agent Remittance Protocol (ARP)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Model Context Protocol: Native](https://img.shields.io/badge/MCP-Native-green.svg)](https://modelcontextprotocol.io/)
[![Circle Grants: Ecosystem Alignment](https://img.shields.io/badge/Circle%20Grants-Ecosystem%20Alignment-purple.svg)](https://www.circle.com/en/grants)

An open-source, non-custodial, consent-enforced execution layer for AI agents routing cross-border stablecoin-to-fiat transactions.

---

## Current Integration Status

- **Wise EUR→KES:** live fiat rail where configured
- **IntaSend / M-Pesa B2C:** integrated for Kenya payout flows
- **Circle StableFX / EURC:** sandbox integrated for EUR→EURC quote testing only
- **Circle production execution:** planned grant milestone
- **Swypt:** USD→USDT→M-Pesa capability confirmed by partner; EURC→M-Pesa in technical validation
- **qwen3.5-flash:** live Qwen Cloud reasoning runtime for hackathon demo
- **Gemini 3.5 Flash:** Gemini reasoning runtime for Google hackathon demo

> **Gemini and Qwen are reference reasoning runtimes. ARP is the deterministic execution and safety layer.** Neither model executes funds — ARP enforces policy, consent, and execution.

---

## 🌐 Overview

The **Agent Remittance Protocol (ARP)** is an asynchronous payment-routing framework designed to bridge autonomous AI agents with stablecoin (USDC/EURC) and fiat payout rails (e.g., Safaricom M-Pesa).

In an era of agentic commerce, autonomous systems must transact across borders without full custody of client funds or direct access to sensitive financial settlement payloads. ARP solves this by enforcing an **isolated execution layer** where LLMs communicate via a standard interface to stage transactions, while a deterministic state machine and cryptographic policy engine govern absolute safety invariants.

### Integration tiers at a glance

| Category | Rails / Components | Status |
| :--- | :--- | :--- |
| **Live production fiat** | Wise (EUR→KES where configured), IntaSend / M-Pesa B2C | Implemented |
| **Sandbox Circle** | Circle StableFX / EURC — EUR→EURC quote testing | Integrated (sandbox) |
| **Planned Circle grant milestones** | StableFX production, EURC-enabled last-mile validation, Circle Wallets Treasury | Planned |
| **Partner last-mile** | Swypt USD→USDT→M-Pesa (confirmed); EURC→M-Pesa (validation) | Partial |
| **Reasoning runtimes** | qwen3.5-flash (Qwen hackathon), Gemini 3.5 Flash (Google hackathon) | Live (reasoning only) |

### 🎯 Circle Ecosystem Value Proposition
* **Programmable Settlement**: Integration blueprints for **Circle Programmable Wallets** (developer-controlled and user-controlled) and Circle minting/redeeming pipelines.
* **On-Chain Attestation**: Incorporates ERC-8004 token standards to anchor agent identity, permission bounds, and compliance credentials on EVM-compatible chains.
* **Capital Efficiency**: Bridges low-cost digital dollars (USDC) into local mobile-money ecosystems (M-Pesa, IntaSend) without intermediary banking hops.
* **Circle StableFX / EURC**: sandbox integrated for EUR→EURC quote testing; production execution planned pending grant / approval.

### 🤖 Model-agnostic reasoning runtimes

ARP supports both **Gemini** and **Qwen** hackathon submissions:

- **qwen3.5-flash** is integrated as the Qwen Cloud reasoning runtime for intent parsing, workflow-step selection, and explanation generation.
- **Gemini 3.5 Flash** serves as the Gemini reasoning runtime for Google hackathon demos.
- **ARP enforces policy and execution.** LLMs propose intents and select tools; the state machine and policy engine control fund movement.

---

## 🚀 Core Features

### 🔒 Non-Custodial Multi-Rail Routing
ARP negotiates real-time, competitive Foreign Exchange (FX) quotes across a dynamic set of payout rails. By decoupling quote discovery from execution, it ensures agents always lock in optimal conversion rates before funds are moved.

**Rail status (accurate as of current integration):**

| Rail | Capability | Status |
| :--- | :--- | :--- |
| **Wise** | EUR→KES fiat corridor | Live where configured |
| **IntaSend** | M-Pesa B2C payout | Integrated |
| **Circle StableFX / EURC** | EUR→EURC quote testing | Sandbox integrated |
| **Swypt** | USD→USDT→M-Pesa | Confirmed by partner |
| **Swypt** | EURC→M-Pesa | In technical validation; direct EURC support not yet confirmed |

Swypt has confirmed live USD→USDT→M-Pesa capability. EURC→M-Pesa is in technical validation; direct EURC support is not yet confirmed. Do not treat Swypt as a confirmed EURC last-mile partner.

### ⚙️ Data-Driven Policy Engines
ARP divides transaction volume and entity risk profiles into four distinct compliance and authorization tiers, ensuring safety across all user classes:
* **Tier-1 (Retail Micro):** Payouts under $250. Simple, single-signature PIN consent enforced via out-of-band communication (e.g., Telegram).
* **Tier-2 (Retail Premium):** Payouts up to $3,000. Requires user wallet signature and verifiable identity attestation JWT.
* **Tier-3 (Corporate Treasury):** Bulk or single-rail corporate transactions up to $20,000. Requires corporate sign-mandates and KYB signatures.
* **Tier-4 (Institutional Hub):** Large-scale settlements up to $1,000,000. Mandates cryptographic multi-sig threshold payloads and on-chain ERC-8004 verification proofs.

### 🤖 Model Context Protocol (MCP) Native
ARP exposes its entire state machine, wallet provisioning, and routing system as standard **Model Context Protocol (MCP)** tools. Any LLM (Claude, GPT, Gemini, Qwen) running an MCP client can immediately discover and interact with the protocol without requiring custom API clients or specialized tool bindings.

---

## 🗺️ Architectural Flow

ARP strictly separates **Agent Intuition** (LLM planning) from **Transactional Guardrails** (Deterministic State Machine). Agents can stage intents, but cannot forge signatures, mutate locked execution states, or bypass policy checks.

```mermaid
sequenceDiagram
    autonumber
    actor User as Human / Client
    participant Agent as LLM Agent (Gemini / Qwen)
    participant MCP as FastMCP Server (ARP)
    participant FSM as State Machine & Policy Engine
    participant Rails as Fiat Rails (Wise / IntaSend) & Sandbox Circle Quotes

    User->>Agent: "Send $100 to +254712345678 in Kenya"
    Agent->>MCP: stage_intent(sender, recipient, source_amount)
    MCP->>FSM: Check Policy & Fetch Rail Quotes
    FSM-->>MCP: Intent Staged (IDLE -> STAGED) & Quote Bound
    MCP-->>Agent: Returns Quote Details & Required Consent Class
    Agent->>User: "Rate: 1 USD = 132.50 KES. Enter PIN to verify."
    User->>MCP: User enters PIN / Submits Consent Token
    MCP->>FSM: execute_transfer(intent_id, consent_token)
    activate FSM
    Note over FSM: Enforces Execution Lock (execution_lock = True)<br/>Transition: STAGED -> AWAITING_PIN -> EXECUTING
    FSM->>Rails: Execute via live fiat rails; Circle StableFX quotes remain sandbox-only
    Rails-->>FSM: Settlement Confirmed (Tx Hash & Receipt minted)
    FSM->>FSM: Mint cryptographic receipt & anchor SHA-256
    deactivate FSM
    FSM-->>MCP: SUCCESS
    MCP-->>Agent: Transfer complete! Receipt ID: rec-xxxxx
    Agent->>User: "Transaction successful! Cash-out optimized recipient payout."
```

### Protocol Invariants & Guardrails
1. **Idempotency Keys (UUID4)**: Generated deterministically during the `STAGED` state. Once bound, they are immutable, preventing accidental double-sends under high-latency network conditions.
2. **Execution Locks**: Transitioning to `EXECUTING` locks all transfer parameters (amounts, assets, recipients) via an atomic lock: `execution_lock = True`. Any alteration attempts throw an `ExecutionLockActiveException`.
3. **No Auto-Retries on Execution Failure**: If an active rail times out during settlement, the state machine enters a terminal `FAILED` state and disables auto-retries. This isolates unstable mobile money API timeouts and forces human-in-the-loop validation, preventing capital loss.
4. **M-Pesa cash-out preservation (ROUND_DOWN / SPLIT / EXACT)**: Calculates safaricom cash-out brackets dynamically so recipients receive exact fiat numbers without residue friction fees.

---

## 📂 Directory Layout

```
ARP/
├── protocol/
│   └── spec.md                # Protocol specifications, invariants & ERC concepts
├── docs/
│   └── legacy/                # Historical draft evidence (not current production claims)
├── src/
│   └── arp/
│       ├── __init__.py        # Package initialization
│       ├── models.py          # Pydantic schemas (Intent, Quote, Principal, Receipt)
│       ├── integrations/
│       │   └── circle_client.py  # Circle Wallets API client (sandbox / planned)
│       ├── state/
│       │   ├── __init__.py
│       │   └── machine.py     # Remittance FSM state transition & locks logic
│       ├── policy/
│       │   ├── __init__.py
│       │   └── engine.py      # Deterministic 4-tier Policy & Compliance Engine
│       └── mcp/
│           ├── __init__.py
│           └── server.py      # FastMCP interface exposing tools to LLM Agents
├── .env.example               # Template for environment configurations
├── LICENSE                    # MIT License open-source specification
├── pyproject.toml             # Package dependencies and installation metadata
└── README.md                  # Comprehensive protocol landing page
```

---

## 🛠️ Getting Started

### 📋 Prerequisites
* **Python 3.11+**
* [uv](https://github.com/astral-sh/uv) or `pip` package manager

### 1. Clone & Setup Workspace
```bash
git clone https://github.com/RemitProtocol/ARP.git
cd ARP
```

### 2. Install Package in Editable Mode
Install the protocol, standard dependencies, and development tools:
```bash
pip install -e .
```
*(Optionally include development dependencies: `pip install -e ".[dev]"`)*

### 3. Environment Configuration
Copy the `.env.example` configuration template and customize your keys:
```bash
cp .env.example .env
```
Open `.env` in your editor and configure your integrations:
* `AGENT_2FA_PIN`: Numeric code used to sign-off Retail Tier transfers.
* `INTASEND_SECRET_KEY`: IntaSend sandboxed API authorization credential.
* `KES_USD_RATE`: Benchmark target FX rate for safe execution checks.

### 4. Running the FastMCP Dev Server
ARP integrates seamlessly with your local development toolsets. Launch the MCP host to start inspecting exposed schema tools:
```bash
mcp dev src/arp/mcp/server.py
```
This spawns the interactive MCP developer server, enabling you to inspect tools (`stage_intent`, `get_routing_quote`, `execute_transfer`, `provision_wallet_on_attestation`), run mock payloads, and analyze client agent logs directly.

---

## 🧪 Verification & Testing

To run the protocol tests and verify FSM and policy engine invariants:

```bash
# Run pytest test suites (if tests are implemented)
pytest

# Auto-format and lint the codebase
black src/
```

---

## 📜 Historical Evidence (Legacy)

Earlier hackathon draft documents with illustrative revenue and execution traces are preserved under [`docs/legacy/`](docs/legacy/). These are labeled **"Historical draft / illustrative evidence — not current Circle production claim."** They must not be interpreted as proof of live Circle EURC / StableFX production settlement.

---

## 🤝 Contributing

We welcome contributions from Web3 core payment engineers, developer advocates, and AI safety researchers.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add support for additional stablecoin corridors'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*Formulated with care for the Circle Grant Committee. Supporting scalable, secure, and compliant agentic remittance infrastructure.*
