"""Runtime mailbox factories for the ESSEMVEE SDR."""

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


class TestRoutedOutlookMailProvider:
    """Real Outlook provider with a fail-closed TEST recipient boundary.

    The orchestrator already isolates TEST-mode recipients. This second boundary
    exists so a future caller cannot accidentally bypass that isolation by
    calling the provider directly with a prospect address.
    """

    provider_name = "outlook_graph_test"

    def __init__(self, mailbox: str, test_recipient: str, *, access_token: str | None = None) -> None:
        recipient = test_recipient.strip().lower()
        if not recipient or "@" not in recipient:
            raise MailboxConfigurationError("A valid test recipient is required")
        self.test_recipient = recipient
        self.mailbox = OutlookGraphMailbox(
            mailbox,
            access_token=access_token,
        )

    def send(self, *, to: str, subject: str, body: str, thread_id: str | None = None) -> SendResult:
        """Send through Outlook, but only to the configured test recipient."""
        if not to or "@" not in to:
            raise MailboxConfigurationError("A valid intended recipient is required")

        # Never trust the caller to have applied TEST-mode isolation correctly.
        # The actual Graph recipient is always the fixed test address.
        result = self.mailbox.send(
            to=self.test_recipient,
            subject=subject,
            body=body,
            thread_id=thread_id,
        )
        return SendResult(
            message_id=result.message_id,
            thread_id=result.thread_id,
            sent_at=result.sent_at,
            provider=self.provider_name,
        )

    def list_inbox_messages(self, *, top: int = 25):
        return self.mailbox.list_inbox_messages(top=top)

    def get_message(self, message_id: str):
        return self.mailbox.get_message(message_id)


def build_mail_provider(*, mode: str | None = None, test_recipient: str | None = None,
                        mailbox: str | None = None, access_token: str | None = None):
    """Build the provider selected by SDR_MODE; TEST remains the safe default.

    TEST mode uses the deterministic provider unless SDR_TEST_OUTLOOK_ENABLED
    is explicitly true. That opt-in is the only path that permits a real Outlook
    API send, and even then the provider is hard-wired to the test recipient.
    """
    selected_mode = (mode or os.getenv("SDR_MODE", TEST_MODE)).strip().lower()
    if selected_mode not in {TEST_MODE, PRODUCTION_MODE}:
        raise ValueError("SDR_MODE must be 'test' or 'production'")

    if selected_mode == TEST_MODE:
        recipient = test_recipient or os.getenv("SDR_TEST_RECIPIENT", "viquar1.08@gmail.com")
        if os.getenv("SDR_TEST_OUTLOOK_ENABLED", "false").strip().lower() in {"1", "true", "yes"}:
            selected_mailbox = mailbox or os.getenv("SDR_MAILBOX")
            if not selected_mailbox:
                raise MailboxConfigurationError(
                    "SDR_MAILBOX is required when SDR_TEST_OUTLOOK_ENABLED=true"
                )
            return TestRoutedOutlookMailProvider(
                selected_mailbox,
                recipient,
                access_token=access_token,
            )
        return TestSDRMailProvider(recipient)

    selected_mailbox = mailbox or os.getenv("SDR_MAILBOX")
    if not selected_mailbox:
        raise MailboxConfigurationError("SDR_MAILBOX is required when SDR_MODE=production")

    return OutlookGraphMailbox(selected_mailbox, access_token=access_token)


__all__ = [
    "TestRoutedOutlookMailProvider",
    "TestSDRMailProvider",
    "TestSend",
    "build_mail_provider",
]
