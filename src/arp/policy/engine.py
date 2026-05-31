from dataclasses import dataclass, field
from enum import Enum
from typing import List
from arp.models import Intent, Principal, PrincipalType

class ConsentClass(str, Enum):
    PIN = "PIN"
    MULTISIG = "MULTISIG"
    RFQ_COUNTERSIGN = "RFQ_COUNTERSIGN"

@dataclass(frozen=True)
class PolicyTier:
    name: str
    max_per_tx: float
    max_per_period: float
    consent_class: ConsentClass
    eligible_rails: List[str]
    required_attestations: List[str] = field(default_factory=list)

# Define stable policy configurations across 4 tiers
TIER_1_RETAIL = PolicyTier(
    name="Tier-1 Retail Micro-Remittance",
    max_per_tx=250.00,  # EUR / USD
    max_per_period=1000.00,
    consent_class=ConsentClass.PIN,
    eligible_rails=["IntaSend", "M-Pesa Direct"],
    required_attestations=["user_wallet_signature"]
)

TIER_2_RETAIL_MEDIUM = PolicyTier(
    name="Tier-2 Retail Premium Remittance",
    max_per_tx=3000.00,
    max_per_period=10000.00,
    consent_class=ConsentClass.PIN,
    eligible_rails=["IntaSend", "Swypt", "Wise"],
    required_attestations=["user_wallet_signature", "identity_attestation_jwt"]
)

TIER_3_CORPORATE = PolicyTier(
    name="Tier-3 Corporate Treasury Operations",
    max_per_tx=20000.00,
    max_per_period=100000.00,
    consent_class=ConsentClass.RFQ_COUNTERSIGN,
    eligible_rails=["Swypt", "Wise", "Circle Settlement"],
    required_attestations=["corporate_sign_mandate_jwt", "kyb_verification_signature"]
)

TIER_4_INSTITUTIONAL = PolicyTier(
    name="Tier-4 Institutional Settlement Hub",
    max_per_tx=1000000.00,
    max_per_period=5000000.00,
    consent_class=ConsentClass.MULTISIG,
    eligible_rails=["Circle Settlement", "Wise Prime"],
    required_attestations=["multisig_threshold_payload", "kyb_verification_signature", "erc8004_validation_proof"]
)

def resolve_tier(intent: Intent, principal: Principal) -> PolicyTier:
    """
    Deterministically resolves the appropriate PolicyTier based on transaction volume, 
    source asset/amount, and sender principal attributes/types.
    """
    amount = intent.source_amount

    if principal.principal_type == PrincipalType.CORPORATE:
        if amount <= 20000.00:
            return TIER_3_CORPORATE
        else:
            return TIER_4_INSTITUTIONAL
    else:  # RETAIL Senders
        if amount <= 250.00:
            return TIER_1_RETAIL
        elif amount <= 3000.00:
            return TIER_2_RETAIL_MEDIUM
        else:
            # High retail transactions require escalation to TIER-3 style policies and manual overrides
            raise ValueError(
                f"Retail intent amount of {amount} exceeds maximal single retail transaction policy boundaries."
            )
