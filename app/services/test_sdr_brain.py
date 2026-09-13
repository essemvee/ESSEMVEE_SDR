"""Integration tests for the SDR execution brain.

These tests use a fake mailbox provider. They never contact a real mailbox.
The production mailbox is deliberately not part of this test suite.
"""

from datetime import datetime, timezone

from app.services.sdr_execution_state import SDRExecutionState, SDRStatus
from app.services.sdr_orchestrator import SDROrchestrator, SendResult


class FakeMailProvider:
    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.counter = 0

    def send(self, *, to, subject, body, thread_id=None):
        self.counter += 1
        message_id = f"test-message-{self.counter}"
        resolved_thread = thread_id or "test-thread-1"
        sent_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.sent.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "thread_id": resolved_thread,
                "message_id": message_id,
            }
        )
        return SendResult(
            message_id=message_id,
            thread_id=resolved_thread,
            sent_at=sent_at,
            provider="fake",
        )


def make_prospect(state: SDRExecutionState):
    key = state.make_prospect_key(
        "CRO Open Data",
        "TEST-12345",
        "cto@example-company.com",
    )
    return state.upsert_prospect(
        prospect_key=key,
        company_name="Example Technology Limited",
        contact_email="cto@example-company.com",
        contact_name="Test CTO",
        contact_role="CTO",
        status=SDRStatus.READY_TO_CONTACT,
    )


def test_test_mode_redirects_real_contact_to_test_recipient():
    with SDRExecutionState(":memory:") as state:
        prospect = make_prospect(state)
        orchestrator = SDROrchestrator(
            state,
            mode="test",
            test_recipient="viquar1.08@gmail.com",
        )

        plan = orchestrator.plan_outbound(prospect)

        assert plan is not None
        assert plan.intended_recipient == "cto@example-company.com"
        assert plan.actual_recipient == "viquar1.08@gmail.com"
        assert plan.test_mode is True


def test_initial_send_persists_message_thread_and_followup():
    with SDRExecutionState(":memory:") as state:
        prospect = make_prospect(state)
        orchestrator = SDROrchestrator(
            state,
            mode="test",
            test_recipient="viquar1.08@gmail.com",
        )
        provider = FakeMailProvider()

        plan = orchestrator.plan_outbound(prospect)
        assert plan is not None

        result = orchestrator.execute_outbound(
            plan,
            provider=provider,
            subject="ESSEMVEE test outreach",
            body="This is a controlled SDR test.",
        )

        updated = state.get_prospect(prospect.prospect_key)
        assert updated is not None
        assert result.message_id == "test-message-1"
        assert updated.thread_id == "test-thread-1"
        assert updated.last_message_id == "test-message-1"
        assert updated.status == SDRStatus.FOLLOWUP_1_DUE
        assert updated.sequence_step == 1
        assert len(provider.sent) == 1
        assert provider.sent[0]["to"] == "viquar1.08@gmail.com"
        assert provider.sent[0]["thread_id"] == "test-thread-1"


def test_positive_reply_stops_outbound_sequence():
    with SDRExecutionState(":memory:") as state:
        prospect = make_prospect(state)
        orchestrator = SDROrchestrator(
            state,
            mode="test",
            test_recipient="viquar1.08@gmail.com",
        )
        provider = FakeMailProvider()
        plan = orchestrator.plan_outbound(prospect)
        assert plan is not None
        orchestrator.execute_outbound(
            plan,
            provider=provider,
            subject="ESSEMVEE test outreach",
            body="This is a controlled SDR test.",
        )

        updated = orchestrator.stop_for_reply(
            prospect.prospect_key,
            reply_message_id="reply-1",
            reply_thread_id="test-thread-1",
            classification=SDRStatus.POSITIVE_REPLY,
            metadata={"test": True},
        )

        assert updated.status == SDRStatus.POSITIVE_REPLY
        assert updated.next_action_at is None
        assert orchestrator.plan_outbound(updated) is None

        events = state.list_events(prospect.prospect_key)
        assert any(event.event_type == "INBOUND_REPLY" for event in events)


def test_unsubscribe_suppresses_future_outreach():
    with SDRExecutionState(":memory:") as state:
        prospect = make_prospect(state)
        orchestrator = SDROrchestrator(
            state,
            mode="test",
            test_recipient="viquar1.08@gmail.com",
        )

        updated = orchestrator.unsubscribe(
            prospect.prospect_key,
            reason="Test unsubscribe",
        )

        assert updated.status == SDRStatus.UNSUBSCRIBED
        assert state.is_suppressed("cto@example-company.com")
        assert orchestrator.plan_outbound(updated) is None


def test_reply_is_idempotent():
    with SDRExecutionState(":memory:") as state:
        prospect = make_prospect(state)
        orchestrator = SDROrchestrator(
            state,
            mode="test",
            test_recipient="viquar1.08@gmail.com",
        )

        first = orchestrator.stop_for_reply(
            prospect.prospect_key,
            reply_message_id="reply-duplicate",
            reply_thread_id="thread-1",
            classification=SDRStatus.NEGATIVE_REPLY,
        )
        second = orchestrator.stop_for_reply(
            prospect.prospect_key,
            reply_message_id="reply-duplicate",
            reply_thread_id="thread-1",
            classification=SDRStatus.NEGATIVE_REPLY,
        )

        assert first.status == SDRStatus.NEGATIVE_REPLY
        assert second.status == SDRStatus.NEGATIVE_REPLY
        inbound = [
            event for event in state.list_events(prospect.prospect_key)
            if event.event_type == "INBOUND_REPLY"
        ]
        assert len(inbound) == 1


def run_all() -> None:
    tests = [
        test_test_mode_redirects_real_contact_to_test_recipient,
        test_initial_send_persists_message_thread_and_followup,
        test_positive_reply_stops_outbound_sequence,
        test_unsubscribe_suppresses_future_outreach,
        test_reply_is_idempotent,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("ALL SDR BRAIN TESTS PASSED")


if __name__ == "__main__":
    run_all()
