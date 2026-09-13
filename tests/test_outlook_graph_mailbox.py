from __future__ import annotations

import json

from app.services.outlook_graph_mailbox import OutlookGraphMailbox
from app.services.sdr_mailbox import MailboxConfigurationError


class FakeResponse:
    def __init__(self, status: int, payload: dict | None = None):
        self.status = status
        self._payload = payload
        self.headers = {}

    def getcode(self):
        return self.status

    def read(self):
        if self._payload is None:
            return b""
        return json.dumps(self._payload).encode("utf-8")


def test_send_uses_provider_contract_and_returns_real_message_id():
    calls = []

    def opener(request, timeout):
        calls.append((request.method, request.full_url, request.data, timeout))
        if request.method == "POST" and request.full_url.endswith("/messages"):
            return FakeResponse(
                201,
                {
                    "id": "AAMK-real-message-id",
                    "conversationId": "conversation-123",
                },
            )
        if request.method == "POST" and request.full_url.endswith("/send"):
            return FakeResponse(202)
        raise AssertionError(f"unexpected request: {request.method} {request.full_url}")

    provider = OutlookGraphMailbox(
        "info@essemvee.com",
        access_token="test-token",
        opener=opener,
    )

    result = provider.send(
        to="viquar1.08@gmail.com",
        subject="Controlled SDR test",
        body="This message must only go to the configured test recipient.",
    )

    assert result.message_id == "AAMK-real-message-id"
    assert result.thread_id == "conversation-123"
    assert result.provider == "outlook_graph"
    assert result.sent_at
    assert len(calls) == 2


def test_send_rejects_invalid_recipient():
    provider = OutlookGraphMailbox(
        "info@essemvee.com",
        access_token="test-token",
        opener=lambda request, timeout: FakeResponse(201, {"id": "unused"}),
    )

    try:
        provider.send(to="", subject="x", body="y")
    except MailboxConfigurationError:
        pass
    else:
        raise AssertionError("invalid recipient must be rejected")
