"""Runtime mailbox factory for the ESSEMVEE SDR."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os

from app.services.outlook_graph_mailbox import OutlookGraphMailbox
from app.services.sdr_mailbox import MailboxConfigurationError
from app.services.sdr_orchestrator import PRODUCTION_MODE, TEST_MODE, SendResult


@dataclass(frozen=True)
class TestSend:
    to: str
    intended_recipient: str
    subject: str
    body: str


class TestSDRMailProvider:
    """Deterministic provider implementing the orchestrator contract."""

    provider_name = "test"

    def __init__(self, test_recipient: str) -> None:
        recipient = test_recipient.strip().lower()
        if not recipient or "@" not in recipient:
            raise MailboxConfigurationError("A valid test recipient is required")
        self.test_recipient = recipient
        self.sent: list[TestSend] = []
        self._counter = 0

    def send(self, *, to: str, subject: str, body: str, thread_id: str | None = None) -> SendResult:
        self._counter += 1
        self.sent.append(TestSend(self.test_recipient, to, subject, body))
        token = f"test-{self._counter}"
        return SendResult(
            message_id=f"{token}-message",
            thread_id=thread_id or f"{token}-thread",
            sent_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            provider=self.provider_name,
        )


def build_mail_provider(*, mode: str | None = None, test_recipient: str | None = None,
                        mailbox: str | None = None, access_token: str | None = None):
    """Build the provider selected by SDR_MODE; TEST is the safe default."""
    selected_mode = (mode or os.getenv("SDR_MODE", TEST_MODE)).strip().lower()
    if selected_mode not in {TEST_MODE, PRODUCTION_MODE}:
        raise ValueError("SDR_MODE must be 'test' or 'production'")

    if selected_mode == TEST_MODE:
        recipient = test_recipient or os.getenv("SDR_TEST_RECIPIENT", "viquar1.08@gmail.com")
        return TestSDRMailProvider(recipient)

    selected_mailbox = mailbox or os.getenv("SDR_MAILBOX")
    if not selected_mailbox:
        raise MailboxConfigurationError("SDR_MAILBOX is required when SDR_MODE=production")

    return OutlookGraphMailbox(selected_mailbox, access_token=access_token)


__all__ = ["TestSDRMailProvider", "TestSend", "build_mail_provider"]
