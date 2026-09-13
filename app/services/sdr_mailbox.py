"""Provider-neutral mailbox contract with a hard TEST-mode recipient guard.

The adapter deliberately contains no credentials and no provider SDK. A real
Outlook/Graph adapter can implement the same protocol later. TEST mode always
redirects delivery to the configured test recipient while retaining the
original recipient in the returned delivery record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


TEST_RECIPIENT = "viquar1.08@gmail.com"


@dataclass(frozen=True)
class OutboundEmail:
    to: str
    subject: str
    body: str
    intended_recipient: str


@dataclass(frozen=True)
class SendResult:
    message_id: str
    thread_id: str
    delivered_to: str
    intended_recipient: str
    mode: str


class MailboxProvider(Protocol):
    def send(self, email: OutboundEmail) -> SendResult:
        """Send an email and return provider identifiers."""


class MailboxConfigurationError(ValueError):
    """Raised when an unsafe or incomplete mailbox configuration is supplied."""


class TestMailboxProvider:
    """Deterministic provider used before a real mailbox is connected."""

    mode = "test"

    def __init__(self, test_recipient: str = TEST_RECIPIENT) -> None:
        if not test_recipient or "@" not in test_recipient:
            raise MailboxConfigurationError("A valid test recipient is required")
        self.test_recipient = test_recipient.strip().lower()
        self.sent: list[OutboundEmail] = []
        self._counter = 0

    def send(self, email: OutboundEmail) -> SendResult:
        self._counter += 1
        redirected = OutboundEmail(
            to=self.test_recipient,
            subject=email.subject,
            body=email.body,
            intended_recipient=email.intended_recipient,
        )
        self.sent.append(redirected)
        token = f"test-{self._counter}"
        return SendResult(
            message_id=f"{token}-message",
            thread_id=f"{token}-thread",
            delivered_to=self.test_recipient,
            intended_recipient=email.intended_recipient,
            mode=self.mode,
        )


class DisabledProductionMailboxProvider:
    """Explicit placeholder preventing accidental live delivery.

    This class exists so production mode cannot silently fall back to a test
    or fake sender. A real provider must be supplied before production is
    enabled.
    """

    mode = "production"

    def send(self, email: OutboundEmail) -> SendResult:
        raise MailboxConfigurationError(
            "Production mailbox provider is not configured. "
            "Connect a real provider before enabling production sending."
        )


__all__ = [
    "DisabledProductionMailboxProvider",
    "MailboxConfigurationError",
    "MailboxProvider",
    "OutboundEmail",
    "SendResult",
    "TEST_RECIPIENT",
    "TestMailboxProvider",
]
