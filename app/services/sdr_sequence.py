"""Deterministic SDR sequence policy.

The sequence engine decides what action is due from persisted state.  It does
not send mail itself; provider integrations will execute the returned action.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.sdr_execution_state import SDRProspect, SDRStatus


@dataclass(frozen=True)
class SDRSequenceStep:
    number: int
    action: str
    sent_status: SDRStatus
    due_status: SDRStatus
    delay_after_previous: timedelta


DEFAULT_SEQUENCE = (
    SDRSequenceStep(
        number=0,
        action="INITIAL_EMAIL",
        sent_status=SDRStatus.EMAIL_SENT,
        due_status=SDRStatus.READY_TO_CONTACT,
        delay_after_previous=timedelta(0),
    ),
    SDRSequenceStep(
        number=1,
        action="FOLLOWUP_1",
        sent_status=SDRStatus.FOLLOWUP_1_SENT,
        due_status=SDRStatus.FOLLOWUP_1_DUE,
        delay_after_previous=timedelta(days=3),
    ),
    SDRSequenceStep(
        number=2,
        action="FOLLOWUP_2",
        sent_status=SDRStatus.FOLLOWUP_2_SENT,
        due_status=SDRStatus.FOLLOWUP_2_DUE,
        delay_after_previous=timedelta(days=4),
    ),
    SDRSequenceStep(
        number=3,
        action="FOLLOWUP_3",
        sent_status=SDRStatus.FOLLOWUP_3_SENT,
        due_status=SDRStatus.FOLLOWUP_3_DUE,
        delay_after_previous=timedelta(days=5),
    ),
)


_STOP_ACTION_STATUSES = frozenset(
    {
        SDRStatus.POSITIVE_REPLY,
        SDRStatus.NEGATIVE_REPLY,
        SDRStatus.UNSUBSCRIBED,
        SDRStatus.BOUNCED,
        SDRStatus.HUMAN_HANDOFF,
        SDRStatus.MEETING_REQUESTED,
        SDRStatus.MEETING_PROPOSED,
        SDRStatus.MEETING_BOOKED,
        SDRStatus.SEQUENCE_COMPLETE,
    }
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def next_followup_status(step_number: int) -> SDRStatus:
    return {
        1: SDRStatus.FOLLOWUP_1_DUE,
        2: SDRStatus.FOLLOWUP_2_DUE,
        3: SDRStatus.FOLLOWUP_3_DUE,
    }[step_number]


def sent_status_for_step(step_number: int) -> SDRStatus:
    return {
        0: SDRStatus.EMAIL_SENT,
        1: SDRStatus.FOLLOWUP_1_SENT,
        2: SDRStatus.FOLLOWUP_2_SENT,
        3: SDRStatus.FOLLOWUP_3_SENT,
    }[step_number]


def next_step_delay(step_number: int) -> timedelta:
    return DEFAULT_SEQUENCE[step_number].delay_after_previous


def action_for(prospect: SDRProspect) -> str | None:
    """Return the provider action allowed by the current persisted status."""
    if prospect.status in _STOP_ACTION_STATUSES:
        return None

    return {
        SDRStatus.READY_TO_CONTACT: "INITIAL_EMAIL",
        SDRStatus.FOLLOWUP_1_DUE: "FOLLOWUP_1",
        SDRStatus.FOLLOWUP_2_DUE: "FOLLOWUP_2",
        SDRStatus.FOLLOWUP_3_DUE: "FOLLOWUP_3",
    }.get(prospect.status)


def schedule_after_send(
    prospect: SDRProspect,
    *,
    sent_at: str | None = None,
) -> tuple[SDRStatus, int, str | None]:
    """Calculate the next persisted state after a successfully sent message."""
    current_step = prospect.sequence_step
    sent_time = parse_timestamp(sent_at) if sent_at else utc_now()

    if current_step == 0:
        next_status = SDRStatus.FOLLOWUP_1_DUE
        next_step = 1
        due_at = sent_time + next_step_delay(1)
    elif current_step == 1:
        next_status = SDRStatus.FOLLOWUP_2_DUE
        next_step = 2
        due_at = sent_time + next_step_delay(2)
    elif current_step == 2:
        next_status = SDRStatus.FOLLOWUP_3_DUE
        next_step = 3
        due_at = sent_time + next_step_delay(3)
    elif current_step == 3:
        next_status = SDRStatus.SEQUENCE_COMPLETE
        next_step = 4
        due_at = None
    else:
        raise ValueError(f"Unsupported SDR sequence step: {current_step}")

    return next_status, next_step, timestamp(due_at) if due_at else None


def mark_due_status(prospect: SDRProspect, *, now: str | None = None) -> SDRStatus:
    """Return the due status implied by the prospect's sequence step."""
    if prospect.status in _STOP_ACTION_STATUSES:
        return prospect.status

    current = parse_timestamp(now) if now else utc_now()
    if prospect.next_action_at is None or parse_timestamp(prospect.next_action_at) > current:
        return prospect.status

    if prospect.sequence_step == 0:
        return SDRStatus.READY_TO_CONTACT
    if prospect.sequence_step in (1, 2, 3):
        return next_followup_status(prospect.sequence_step)
    return SDRStatus.SEQUENCE_COMPLETE


__all__ = [
    "DEFAULT_SEQUENCE",
    "SDRSequenceStep",
    "action_for",
    "mark_due_status",
    "next_followup_status",
    "next_step_delay",
    "parse_timestamp",
    "schedule_after_send",
    "sent_status_for_step",
    "timestamp",
]
