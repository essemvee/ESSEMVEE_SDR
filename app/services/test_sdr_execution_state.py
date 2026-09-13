"""Tests for the persistent SDR execution state engine."""

from datetime import datetime, timedelta, timezone

from app.services.sdr_execution_state import (
    SDRExecutionState,
    SDRStatus,
)
from app.services.sdr_sequence import (
    action_for,
    schedule_after_send,
    timestamp,
)


def test_persisted_prospect_and_idempotent_event() -> None:
    state = SDRExecutionState(":memory:")
    key = state.make_prospect_key("CRO Open Data", 12345, "cto@example.com")

    prospect = state.upsert_prospect(
        prospect_key=key,
        company_name="Example Technology Limited",
        contact_email="cto@example.com",
        contact_name="Example CTO",
        contact_role="CTO",
        status=SDRStatus.READY_TO_CONTACT,
    )

    assert prospect.status is SDRStatus.READY_TO_CONTACT
    assert state.count() == 1

    assert state.record_event(
        key,
        "EMAIL_APPROVED",
        idempotency_key="approval-1",
    ) is True
    assert state.record_event(
        key,
        "EMAIL_APPROVED",
        idempotency_key="approval-1",
    ) is False
    assert len(state.list_events(key)) == 1
    state.close()


def test_transition_stops_future_action() -> None:
    state = SDRExecutionState(":memory:")
    key = "prospect-stop"
    state.upsert_prospect(
        prospect_key=key,
        company_name="Example",
        contact_email="cto@example.com",
        status=SDRStatus.FOLLOWUP_1_DUE,
        next_action_at=timestamp(datetime.now(timezone.utc) - timedelta(minutes=1)),
    )

    state.transition(
        key,
        SDRStatus.UNSUBSCRIBED,
        stop_reason="Prospect requested no further contact",
    )
    prospect = state.get_prospect(key)
    assert prospect is not None
    assert prospect.status is SDRStatus.UNSUBSCRIBED
    assert prospect.next_action_at is None
    assert state.due_prospects() == []
    state.close()


def test_message_idempotency_and_thread_persistence() -> None:
    state = SDRExecutionState(":memory:")
    key = "prospect-message"
    state.upsert_prospect(
        prospect_key=key,
        company_name="Example",
        contact_email="cto@example.com",
        status=SDRStatus.READY_TO_CONTACT,
    )

    assert state.record_message(
        message_id="msg-1",
        prospect_key=key,
        direction="OUTBOUND",
        provider="test",
        thread_id="thread-1",
        sent_at="2026-09-13T10:00:00+00:00",
    ) is True
    assert state.record_message(
        message_id="msg-1",
        prospect_key=key,
        direction="OUTBOUND",
        provider="test",
        thread_id="thread-1",
    ) is False

    prospect = state.get_prospect(key)
    assert prospect is not None
    assert prospect.thread_id == "thread-1"
    assert prospect.last_message_id == "msg-1"
    state.close()


def test_sequence_advances_and_finishes() -> None:
    state = SDRExecutionState(":memory:")
    key = "prospect-sequence"
    state.upsert_prospect(
        prospect_key=key,
        company_name="Example",
        contact_email="cto@example.com",
        status=SDRStatus.READY_TO_CONTACT,
        sequence_step=0,
    )
    prospect = state.get_prospect(key)
    assert prospect is not None
    assert action_for(prospect) == "INITIAL_EMAIL"

    for expected_status, expected_step in (
        (SDRStatus.FOLLOWUP_1_DUE, 1),
        (SDRStatus.FOLLOWUP_2_DUE, 2),
        (SDRStatus.FOLLOWUP_3_DUE, 3),
        (SDRStatus.SEQUENCE_COMPLETE, 4),
    ):
        new_status, new_step, due_at = schedule_after_send(
            prospect,
            sent_at="2026-09-13T10:00:00+00:00",
        )
        assert new_status is expected_status
        assert new_step == expected_step
        state.transition(
            key,
            new_status,
            sequence_step=new_step,
            next_action_at=due_at,
        )
        prospect = state.get_prospect(key)
        assert prospect is not None

    assert prospect.status is SDRStatus.SEQUENCE_COMPLETE
    assert prospect.next_action_at is None
    state.close()


if __name__ == "__main__":
    test_persisted_prospect_and_idempotent_event()
    test_transition_stops_future_action()
    test_message_idempotency_and_thread_persistence()
    test_sequence_advances_and_finishes()
    print("ALL SDR EXECUTION STATE TESTS PASSED")
