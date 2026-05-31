import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from arp.models import Intent, StateEnum

class StateMachineException(Exception):
    """Base class for all State Machine transition exceptions."""
    pass

class IllegalStateTransitionException(StateMachineException):
    """Thrown when attempting a transition not permitted by the FSM."""
    pass

class ExecutionLockActiveException(StateMachineException):
    """Thrown when attempting to mutate an intent when execution_lock is True."""
    pass

class IntentExpiredException(StateMachineException):
    """Thrown when performing operations on an intent that has expired."""
    pass

class MissingConsentException(StateMachineException):
    """Thrown when executing without valid consent tokens."""
    pass

class RemittanceStateMachine:
    def __init__(self):
        # In-memory storage for intent state tracking and locks
        self._intents: Dict[UUID, Intent] = {}
        self._state_durations: Dict[UUID, datetime] = {}
        # Durations for state expiration
        self.staged_timeout = timedelta(minutes=5)
        self.awaiting_pin_timeout = timedelta(minutes=2)

    def register_intent(self, intent: Intent) -> None:
        """Registers a new intent in the state machine context."""
        self._intents[intent.idempotency_key] = intent
        self._state_durations[intent.idempotency_key] = datetime.utcnow()

    def get_intent(self, intent_id: UUID) -> Intent:
        """Retrieves and evaluates active timeout validations before returning the intent."""
        if intent_id not in self._intents:
            raise StateMachineException(f"Intent with ID {intent_id} not found.")
        
        intent = self._intents[intent_id]
        self._check_timeouts(intent)
        return intent

    def _check_timeouts(self, intent: Intent) -> None:
        """Verifies state timers. STAGED expires in 5 mins, AWAITING_PIN in 2 mins."""
        if intent.state in [StateEnum.SUCCESS, StateEnum.FAILED]:
            return

        entry_time = self._state_durations.get(intent.idempotency_key, intent.created_at)
        now = datetime.utcnow()

        if intent.state == StateEnum.STAGED:
            if now - entry_time > self.staged_timeout:
                intent.state = StateEnum.FAILED
                intent.execution_lock = False
                raise IntentExpiredException(f"Intent {intent.idempotency_key} expired in STAGED state.")
        
        elif intent.state == StateEnum.AWAITING_PIN:
            if now - entry_time > self.awaiting_pin_timeout:
                intent.state = StateEnum.FAILED
                intent.execution_lock = False
                raise IntentExpiredException(f"Intent {intent.idempotency_key} expired in AWAITING_PIN state.")

    async def transition_to_staged(self, intent_id: UUID, quote_id: str) -> Intent:
        """Transitions intent from IDLE to STAGED and binds a quote."""
        intent = self.get_intent(intent_id)
        
        if intent.execution_lock:
            raise ExecutionLockActiveException("Cannot modify active execution transaction parameters.")
            
        if intent.state != StateEnum.IDLE:
            raise IllegalStateTransitionException(f"Cannot transition to STAGED from {intent.state}.")

        intent.state = StateEnum.STAGED
        intent.quote_id = quote_id
        self._state_durations[intent_id] = datetime.utcnow()
        return intent

    async def transition_to_awaiting_pin(self, intent_id: UUID) -> Intent:
        """Transitions intent from STAGED to AWAITING_PIN."""
        intent = self.get_intent(intent_id)
        
        if intent.execution_lock:
            raise ExecutionLockActiveException("Cannot modify active execution transaction parameters.")
            
        if intent.state != StateEnum.STAGED:
            raise IllegalStateTransitionException(f"Cannot transition to AWAITING_PIN from {intent.state}.")

        intent.state = StateEnum.AWAITING_PIN
        self._state_durations[intent_id] = datetime.utcnow()
        return intent

    async def transition_to_executing(self, intent_id: UUID, consent_token: Optional[str] = None, requires_consent: bool = True) -> Intent:
        """Transitions intent to EXECUTING, locking all parameters."""
        intent = self.get_intent(intent_id)
        
        if intent.execution_lock:
            raise ExecutionLockActiveException("Execution lock is already active for this transaction.")

        if intent.state not in [StateEnum.STAGED, StateEnum.AWAITING_PIN]:
            raise IllegalStateTransitionException(f"Cannot transition to EXECUTING from {intent.state}.")

        if requires_consent and not consent_token:
            raise MissingConsentException("Cryptographic human consent token is mandatory for execution.")

        # Set atomic lock immediately
        intent.execution_lock = True
        intent.state = StateEnum.EXECUTING
        self._state_durations[intent_id] = datetime.utcnow()
        return intent

    async def finalize_transaction(self, intent_id: UUID, success: bool) -> Intent:
        """Transitions intent from EXECUTING to terminal SUCCESS or FAILED state."""
        intent = self.get_intent(intent_id)
        
        if intent.state != StateEnum.EXECUTING:
            raise IllegalStateTransitionException(f"Cannot finalize transaction from state: {intent.state}")

        intent.state = StateEnum.SUCCESS if success else StateEnum.FAILED
        # Unlock execution on finalize
        intent.execution_lock = False
        self._state_durations[intent_id] = datetime.utcnow()
        return intent
