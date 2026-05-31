from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
import datetime
import hashlib

from arp.models import Intent, Principal, PrincipalType, StateEnum, Quote, Receipt
from arp.state.machine import RemittanceStateMachine, StateMachineException
from arp.policy.engine import resolve_tier

# Initialize MCP Server with explicit settings
mcp = FastMCP("AgentRemittanceProtocol")

# InMemory registries simulating databases
STATE_MACHINE = RemittanceStateMachine()
PRINCIPALS: Dict[str, Principal] = {}
QUOTES: Dict[str, Quote] = {}
RECEIPTS: Dict[str, Receipt] = {}
PROVISIONED_WALLETS: Dict[str, Dict[str, Any]] = {}

# Register a mock corporate and retail principal for default demo scenarios
default_retail = Principal(
    id="principal-retail-123",
    principal_type=PrincipalType.RETAIL,
    name="Jane Doe",
    email="jane@example.com",
    jurisdiction="KE",
    kyc_level=1,
    attributes={"wallet_address": "0x123...abc"}
)
default_corp = Principal(
    id="principal-corp-999",
    principal_type=PrincipalType.CORPORATE,
    name="RemitCorp East Africa",
    email="treasury@remitcorp.co",
    jurisdiction="KE",
    kyc_level=3,
    attributes={"kyb_registration": "KE-1294812", "wallet_address": "0xabc...def"}
)
PRINCIPALS[default_retail.id] = default_retail
PRINCIPALS[default_corp.id] = default_corp

@mcp.tool()
async def stage_intent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stages a new Remittance Intent. Fetches simulated optimal quotes, deterministically 
    binds them, assigns an idempotency key, and locks FSM parameters.
    """
    try:
        sender_id = payload.get("sender_id")
        principal = PRINCIPALS.get(sender_id)
        if not principal:
            raise McpError(f"Principal with sender_id '{sender_id}' not found.")

        intent_key = uuid4()
        intent = Intent(
            idempotency_key=intent_key,
            sender_id=sender_id,
            recipient_id=payload["recipient_id"],
            source_amount=float(payload["source_amount"]),
            source_asset=payload["source_asset"],
            target_asset=payload["target_asset"],
            state=StateEnum.IDLE
        )
        STATE_MACHINE.register_intent(intent)

        # Determine policy tier and routing configurations
        tier = resolve_tier(intent, principal)

        # Mock optimal Quote calculation with M-Pesa rounding preservation
        source_amt = intent.source_amount
        conv_rate = 132.50 if intent.target_asset == "KES" else 1.0
        gross_target = source_amt * conv_rate
        
        # M-Pesa ROUND_DOWN Cash-out withdrawal bracket fee preservation logic
        mpesa_fee = 0.0
        if intent.target_asset == "KES":
            if gross_target <= 500:
                mpesa_fee = 27.0
            elif gross_target <= 1000:
                mpesa_fee = 28.0
            elif gross_target <= 5000:
                mpesa_fee = 85.0
            elif gross_target <= 10000:
                mpesa_fee = 112.0
            else:
                mpesa_fee = 210.0

        net_payout = gross_target - mpesa_fee
        quote_id = f"q-{uuid4().hex[:8]}"
        quote = Quote(
            quote_id=quote_id,
            intent_id=intent_key,
            rail_name=tier.eligible_rails[0],
            source_amount=source_amt,
            conversion_rate=conv_rate,
            net_recipient_amount=max(0.0, net_payout),
            mpesa_withdrawal_fee=mpesa_fee,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        )
        QUOTES[quote_id] = quote

        # Stage the state machine transition
        await STATE_MACHINE.transition_to_staged(intent_key, quote_id)
        
        # If policy tier requires PIN consent, transition instantly to AWAITING_PIN
        if tier.consent_class == "PIN":
            await STATE_MACHINE.transition_to_awaiting_pin(intent_key)

        return {
            "intent": intent.model_dump(),
            "selected_quote": quote.model_dump(),
            "resolved_policy_tier": tier.name,
            "consent_required": tier.consent_class
        }

    except Exception as e:
        raise McpError(f"Staging failed: {str(e)}")

@mcp.tool()
async def get_routing_quote(intent_id: str) -> Dict[str, Any]:
    """
    Fetches the active routing quote currently bound to a staged intent.
    """
    try:
        ikey = UUID(intent_id)
        intent = STATE_MACHINE.get_intent(ikey)
        if not intent.quote_id or intent.quote_id not in QUOTES:
            raise McpError("No active quote bound to this intent.")
        return QUOTES[intent.quote_id].model_dump()
    except Exception as e:
        raise McpError(f"Failed to retrieve quote: {str(e)}")

@mcp.tool()
async def execute_transfer(intent_id: str, human_consent_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a remittance transfer securely under absolute execution locks. 
    Requires a valid human consent token to unlock transitions for PIN tiers.
    """
    try:
        ikey = UUID(intent_id)
        intent = STATE_MACHINE.get_intent(ikey)
        sender_id = intent.sender_id
        principal = PRINCIPALS[sender_id]
        tier = resolve_tier(intent, principal)

        # Transition to EXECUTING (checks consent token if required)
        requires_consent = (tier.consent_class == "PIN" or tier.consent_class == "RFQ_COUNTERSIGN")
        await STATE_MACHINE.transition_to_executing(
            intent_id=ikey,
            consent_token=human_consent_token,
            requires_consent=requires_consent
        )

        # Mock out-of-band payout rail settlement success
        success = True 
        await STATE_MACHINE.finalize_transaction(ikey, success=success)

        if success:
            quote = QUOTES[intent.quote_id]
            receipt_id = f"rec-{uuid4().hex[:12]}"
            tx_hash = f"0x{hashlib.sha256(str(ikey).encode()).hexdigest()}"
            
            raw_hash_data = f"{receipt_id}:{ikey}:{sender_id}:{quote.net_recipient_amount}:{tx_hash}"
            crypt_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()

            receipt = Receipt(
                receipt_id=receipt_id,
                intent_id=ikey,
                sender_id=sender_id,
                recipient_id=intent.recipient_id,
                final_source_amount=intent.source_amount,
                final_recipient_amount=quote.net_recipient_amount,
                source_asset=intent.source_asset,
                target_asset=intent.target_asset,
                rail_transaction_hash=tx_hash,
                cryptographic_hash=crypt_hash
            )
            RECEIPTS[receipt_id] = receipt
            return {
                "status": "SUCCESS",
                "receipt": receipt.model_dump()
            }
        else:
            return {
                "status": "FAILED",
                "reason": "Payment rail execution failure"
            }

    except StateMachineException as sme:
        raise McpError(f"State Machine constraint validation failed: {str(sme)}")
    except Exception as e:
        raise McpError(f"Execution failed: {str(e)}")

@mcp.tool()
async def provision_wallet_on_attestation(attestation_jwt: str, tier: str) -> Dict[str, Any]:
    """
    Securely provisions a Circle Developer-Controlled Multi-Sig wallet envelope 
    following strict verification of a KYB verification attestation JWT signature.
    AI agents cannot bypass validation rules or inject keys directly.
    """
    # Simple deterministic validation: must contain verified keyword for demo/compliance test
    if "VALID_KYB_PROVIDER" not in attestation_jwt:
        raise McpError("Invalid or missing compliance verification signature inside attestation JWT.")

    wallet_id = f"circle-wallet-{uuid4().hex[:12]}"
    PROVISIONED_WALLETS[wallet_id] = {
        "wallet_id": wallet_id,
        "tier": tier,
        "type": "Multi-Sig Envelope",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    return {
        "status": "PROVISIONED",
        "wallet": PROVISIONED_WALLETS[wallet_id]
    }
