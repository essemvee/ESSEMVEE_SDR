"""Safe in-memory mailbox provider for SDR TEST mode.

This provider implements the existing MailProvider contract used by
SDROrchestrator. It never sends network mail. Every outbound address is
redirected to TEST_RECIPIENT while the orchestrator records the intended
recipient separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.sdr_mailbox import TEST_RECIPIENT
from app.services.sdr_orchestrator import SendResult


@dataclass(frozen=True)
class TestSentMessage:
    message_id: str
    thread_id: str
    to: str
    subject: str
    body: str


class InMemoryTestMailbox:
    """Deterministic, network-free implementation of MailProvider."""

    def __init__(self, recipient: str = TEST_RECIPIENT) -> None:
        self.recipient = recipient.strip().lower()
        if not self.recipient or "@" not in self.recipient:
            raise ValueError("A valid TEST recipient is required")
        self.messages: list[TestSentMessage] = []

    def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> SendResult:
        sequence = len(self.messages) + 1
        message_id = f"test-message-{sequence}"
        actual_thread = thread_id or f"test-thread-{sequence}"
        self.messages.append(
            TestSentMessage(
                message_id=message_id,
                thread_id=actual_thread,
                to=self.recipient,
                subject=subject,
                body=body,
            )
        )
        return SendResult(
            message_id=message_id,
            thread_id=actual_thread,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            provider="in-memory-test-mailbox",
        )


__all__ = ["InMemoryTestMailbox", "TestSentMessage"]
