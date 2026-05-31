from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class StateEnum(str, Enum):
    IDLE = "IDLE"
    STAGED = "STAGED"
    AWAITING_PIN = "AWAITING_PIN"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PrincipalType(str, Enum):
    RETAIL = "RETAIL"
    CORPORATE = "CORPORATE"

class Principal(BaseModel):
    id: str = Field(..., description="Unique identifier of the principal (sender)")
    principal_type: PrincipalType = Field(..., description="Type of principal: RETAIL or CORPORATE")
    name: str = Field(..., description="Legal name of the sender entity or individual")
    email: EmailStr = Field(..., description="Verified email address of the principal")
    jurisdiction: str = Field(..., description="ISO 3166-1 alpha-2 country code (e.g. KE, US, DE)")
    kyc_level: int = Field(default=1, description="KYC verification tier (e.g. 1, 2, 3)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Metadata and jurisdictional verification attributes")

class Intent(BaseModel):
    idempotency_key: UUID = Field(default_factory=uuid4, description="Deterministic transaction idempotency key")
    sender_id: str = Field(..., description="Reference to the Principal ID")
    recipient_id: str = Field(..., description="Reference identifier for the recipient (e.g., M-Pesa phone number)")
    source_amount: float = Field(..., description="Source remittance value")
    source_asset: str = Field(..., description="Source currency or stablecoin (e.g., USDC, EURC)")
    target_asset: str = Field(..., description="Target currency or asset (e.g., KES, EUR)")
    state: StateEnum = Field(default=StateEnum.IDLE, description="FSM Transaction State")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    quote_id: Optional[str] = Field(default=None, description="Linked dynamic quote ID once STAGED")
    execution_lock: bool = Field(default=False, description="Atomic lock preventing mutation during active execution")

class Quote(BaseModel):
    quote_id: str = Field(..., description="Unique quote identifier from payout rails")
    intent_id: UUID = Field(..., description="Linked remittance intent ID")
    rail_name: str = Field(..., description="Target rail name (e.g., Wise, IntaSend, Swypt)")
    source_amount: float = Field(..., description="Gross send amount from source wallet")
    conversion_rate: float = Field(..., description="Guaranteed FX rate")
    net_recipient_amount: float = Field(..., description="Final net amount received by destination after all deductions")
    gas_fee_source: float = Field(default=0.0, description="On-chain network gas estimate in source asset")
    rail_fee: float = Field(default=0.0, description="Payment rail transaction charges")
    mpesa_withdrawal_fee: float = Field(default=0.0, description="Estimated cash-out withdrawal fee for M-Pesa recipient")
    spread_fee: float = Field(default=0.0, description="Liquidity provider margin spread")
    expires_at: datetime = Field(..., description="Expiration timestamp of the quote")

class Receipt(BaseModel):
    receipt_id: str = Field(..., description="Unique receipt identifier")
    intent_id: UUID = Field(..., description="Idempotency key / Intent ID of the remittance")
    sender_id: str = Field(..., description="Sender principal identifier")
    recipient_id: str = Field(..., description="Recipient identifier")
    final_source_amount: float = Field(..., description="Final debited source amount")
    final_recipient_amount: float = Field(..., description="Final payout amount")
    source_asset: str = Field(..., description="Source asset token")
    target_asset: str = Field(..., description="Target payout asset")
    rail_transaction_hash: str = Field(..., description="On-chain / rail-specific settlement hash or reference")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")
    cryptographic_hash: str = Field(..., description="SHA-256 hash of receipt attributes designed to be anchored on-chain")
