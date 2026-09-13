"""Execution controller for the ESSEMVEE autonomous SDR.

The orchestrator is deliberately provider-agnostic.  It decides whether an
outbound action is permitted, applies TEST-mode recipient isolation, and
persists the result.  A future mailbox adapter supplies the actual send,
reply, and calendar operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Protocol

from app.services.sdr_execution_state import (
    SDRExecutionState,
    SDRProspect,
    SDRStatus,
)
from app.services.sdr_sequence import action_for, schedule_after_send


TEST_MODE = "test"
PRODUCTION_MODE = "production"


class MailProvider(Protocol):
    def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> "SendResult": ...


@dataclass(frozen=True)
class SendResult:
    message_id: str
    thread_id: str | None
    sent_at: str
    provider: str


@dataclass(frozen=True)
class OutboundPlan:
    prospect_key: str
    action: str
    step: int
    intended_recipient: str
    actual_recipient: str
    test_mode: bool


class SDROrchestrator:
    """Coordinates persistent SDR state with a future mailbox provider."""

    def __init__(
        self,
        state: SDRExecutionState,
        *,
        mode: str | None = None,
        test_recipient: str | None = None,
    ) -> None:
        selected_mode = (mode or os.getenv("SDR_MODE", TEST_MODE)).strip().lower()
        if selected_mode not in {TEST_MODE, PRODUCTION_MODE}:
            raise ValueError("SDR_MODE must be 'test' or 'production'")

        recipient = test_recipient or os.getenv(
            "SDR_TEST_RECIPIENT",
            "viquar1.08@gmail.com",
        )
        if selected_mode == TEST_MODE and not recipient:
            raise ValueError("A test recipient is required in TEST mode")

        self.state = state
        self.mode = selected_mode
        self.test_recipient = recipient

    @property
    def test_mode(self) -> bool:
        return self.mode == TEST_MODE

    def plan_outbound(self, prospect: SDRProspect) -> OutboundPlan | None:
        """Create a safe outbound plan without sending anything."""
        action = action_for(prospect)
        if action is None:
            return None

        if not prospect.contact_email:
            raise ValueError("Outbound action requires a verified contact email")

        if self.state.is_suppressed(prospect.contact_email):
            return None

        return OutboundPlan(
            prospect_key=prospect.prospect_key,
            action=action,
            step=prospect.sequence_step,
            intended_recipient=prospect.contact_email,
            actual_recipient=(self.test_recipient if self.test_mode else prospect.contact_email),
            test_mode=self.test_mode,
        )

    def execute_outbound(
        self,
        plan: OutboundPlan,
        *,
        provider: MailProvider,
        subject: str,
        body: str,
    ) -> SendResult:
        """Send one planned message and atomically persist its sequence result."""
        prospect = self.state.get_prospect(plan.prospect_key)
        if prospect is None:
            raise KeyError(f"Unknown SDR prospect: {plan.prospect_key}")

        current_plan = self.plan_outbound(prospect)
        if current_plan != plan:
            raise RuntimeError("Outbound plan is stale; re-read SDR state before sending")

        result = provider.send(
            to=plan.actual_recipient,
            subject=subject,
            body=body,
            thread_id=prospect.thread_id,
        )

        self.state.record_message(
            message_id=result.message_id,
            prospect_key=plan.prospect_key,
            direction="OUTBOUND",
            provider=result.provider,
            thread_id=result.thread_id,
            sent_at=result.sent_at,
            subject=subject,
            status="SENT",
        )

        next_status, next_step, next_action_at = schedule_after_send(
            prospect,
            sent_at=result.sent_at,
        )

        self.state.transition(
            plan.prospect_key,
            next_status,
            sequence_step=next_step,
            next_action_at=next_action_at,
            event_type="OUTBOUND_SENT",
            metadata={
                "action": plan.action,
                "step": plan.step,
                "intended_recipient": plan.intended_recipient,
                "actual_recipient": plan.actual_recipient,
                "test_mode": plan.test_mode,
                "message_id": result.message_id,
                "thread_id": result.thread_id,
            },
            idempotency_key=f"outbound:{result.message_id}",
        )

        return result

    def stop_for_reply(
        self,
        prospect_key: str,
        *,
        reply_message_id: str,
        reply_thread_id: str | None,
        classification: SDRStatus,
        metadata: dict | None = None,
    ) -> SDRProspect:
        """Persist an inbound reply and stop outbound sequencing when required."""
        if classification not in {
            SDRStatus.POSITIVE_REPLY,
            SDRStatus.NEGATIVE_REPLY,
            SDRStatus.MEETING_REQUESTED,
            SDRStatus.MEETING_PROPOSED,
            SDRStatus.MEETING_BOOKED,
        }:
            raise ValueError("Invalid reply classification")

        prospect = self.state.get_prospect(prospect_key)
        if prospect is None:
            raise KeyError(f"Unknown SDR prospect: {prospect_key}")

        inserted = self.state.record_message(
            message_id=reply_message_id,
            prospect_key=prospect_key,
            direction="INBOUND",
            thread_id=reply_thread_id,
            received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            status="RECEIVED",
        )
        if not inserted:
            return self.state.get_prospect(prospect_key)  # type: ignore[return-value]

        return self.state.transition(
            prospect_key,
            classification,
            event_type="INBOUND_REPLY",
            metadata=metadata or {},
            idempotency_key=f"reply:{reply_message_id}",
        )

    def unsubscribe(self, prospect_key: str, *, reason: str = "Prospect unsubscribed") -> SDRProspect:
        prospect = self.state.get_prospect(prospect_key)
        if prospect is None:
            raise KeyError(f"Unknown SDR prospect: {prospect_key}")
        if prospect.contact_email:
            self.state.add_suppression(prospect.contact_email, "EMAIL", reason=reason)
        return self.state.transition(
            prospect_key,
            SDRStatus.UNSUBSCRIBED,
            stop_reason=reason,
            event_type="UNSUBSCRIBED",
        )


__all__ = [
    "MailProvider",
    "OutboundPlan",
    "PRODUCTION_MODE",
    "SDROrchestrator",
    "SendResult",
    "TEST_MODE",
]
