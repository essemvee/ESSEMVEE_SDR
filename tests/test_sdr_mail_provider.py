import json

import pytest

from app.services.outlook_graph_mailbox import OutlookGraphMailbox
from app.services.sdr_mail_provider import (
    TestRoutedOutlookMailProvider,
    TestSDRMailProvider,
    build_mail_provider,
)
from app.services.sdr_mailbox import MailboxConfigurationError


class FakeResponse:
    def __init__(self, payload=None, status=201):
        self.status = status
        self._payload = payload
        self.headers = {}

    def getcode(self):
        return self.status

    def read(self):
        return b"" if self._payload is None else json.dumps(self._payload).encode()


def test_test_mode_never_constructs_graph_provider(monkeypatch):
    monkeypatch.delenv("MICROSOFT_GRAPH_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SDR_TEST_OUTLOOK_ENABLED", raising=False)
    provider = build_mail_provider(mode="test", test_recipient="test@example.com")

    assert isinstance(provider, TestSDRMailProvider)
    assert not isinstance(provider, OutlookGraphMailbox)

    result = provider.send(
        to="prospect@example.com",
        subject="Test",
        body="Hello",
    )

    assert provider.sent[0].to == "test@example.com"
    assert provider.sent[0].intended_recipient == "prospect@example.com"
    assert result.provider == "test"


def test_production_requires_mailbox(monkeypatch):
    monkeypatch.delenv("SDR_MAILBOX", raising=False)
    monkeypatch.delenv("MICROSOFT_GRAPH_ACCESS_TOKEN", raising=False)

    with pytest.raises(MailboxConfigurationError, match="SDR_MAILBOX"):
        build_mail_provider(mode="production")


def test_production_constructs_graph_provider_with_explicit_credentials():
    provider = build_mail_provider(
        mode="production",
        mailbox="info@essemvee.com",
        access_token="fake-token",
    )

    assert isinstance(provider, OutlookGraphMailbox)
    assert provider.mailbox == "info@essemvee.com"


def test_test_outlook_mode_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SDR_TEST_OUTLOOK_ENABLED", "true")
    monkeypatch.delenv("SDR_MAILBOX", raising=False)

    with pytest.raises(MailboxConfigurationError, match="SDR_MAILBOX"):
        build_mail_provider(
            mode="test",
            test_recipient="viquar1.08@gmail.com",
            access_token="fake-token",
        )


def test_test_routed_outlook_forces_test_recipient(monkeypatch):
    calls = []

    def opener(request, timeout):
        calls.append((request.method, request.full_url, json.loads(request.data) if request.data else None))
        if request.full_url.endswith("/messages"):
            return FakeResponse(
                {
                    "id": "graph-message-1",
                    "conversationId": "graph-thread-1",
                },
                201,
            )
        if request.full_url.endswith("/messages/graph-message-1/send"):
            return FakeResponse(None, 202)
        raise AssertionError(f"Unexpected Graph request: {request.method} {request.full_url}")

    mailbox = OutlookGraphMailbox(
        "info@essemvee.com",
        access_token="fake-token",
        opener=opener,
    )
    provider = TestRoutedOutlookMailProvider.__new__(TestRoutedOutlookMailProvider)
    provider.test_recipient = "viquar1.08@gmail.com"
    provider.mailbox = mailbox

    result = provider.send(
        to="real-prospect@example.com",
        subject="Controlled test",
        body="This must only reach the test mailbox.",
    )

    create_call = calls[0]
    payload = create_call[2]
    assert payload["toRecipients"][0]["emailAddress"]["address"] == "viquar1.08@gmail.com"
    assert "real-prospect@example.com" not in json.dumps(payload)
    assert result.message_id == "graph-message-1"
    assert result.thread_id == "graph-thread-1"
    assert result.provider == "outlook_graph_test"
