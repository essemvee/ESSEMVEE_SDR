"""Network-free tests for the Microsoft Graph mailbox adapter."""

from __future__ import annotations

import io
import json

from app.services.outlook_graph_mailbox import OutlookGraphMailbox
from app.services.sdr_mailbox import OutboundEmail


class FakeResponse:
    def __init__(self, status: int, payload: dict | None = None) -> None:
        self.status = status
        self._payload = payload
        self.headers = {}

    def getcode(self):
        return self.status

    def read(self):
        if self._payload is None:
            return b""
        return json.dumps(self._payload).encode("utf-8")


class FakeOpener:
    def __init__(self) -> None:
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        if request.method == "POST" and request.full_url.endswith("/sendMail"):
            return FakeResponse(202)
        if "/mailFolders/inbox/messages" in request.full_url:
            return FakeResponse(
                200,
                {
                    "value": [
                        {
                            "id": "graph-message-1",
                            "conversationId": "conversation-1",
                            "internetMessageId": "<internet-1>",
                            "subject": "Re: ESSEMVEE",
                            "from": {"emailAddress": {"address": "cto@example.com"}},
                            "receivedDateTime": "2026-09-13T15:00:00Z",
                            "body": {"contentType": "text", "content": "Interested."},
                        }
                    ]
                },
            )
        if "/messages/graph-message-1" in request.full_url:
            return FakeResponse(
                200,
                {
                    "id": "graph-message-1",
                    "conversationId": "conversation-1",
                    "internetMessageId": "<internet-1>",
                    "subject": "Re: ESSEMVEE",
                    "from": {"emailAddress": {"address": "cto@example.com"}},
                    "receivedDateTime": "2026-09-13T15:00:00Z",
                    "body": {"contentType": "text", "content": "Interested."},
                },
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.full_url}")


def make_mailbox(opener: FakeOpener) -> OutlookGraphMailbox:
    return OutlookGraphMailbox(
        "info@essemvee.com",
        access_token="test-token",
        graph_base_url="https://graph.test/v1.0",
        opener=opener,
    )


def test_send_uses_configured_mailbox_and_preserves_intended_recipient():
    opener = FakeOpener()
    mailbox = make_mailbox(opener)
    result = mailbox.send(
        OutboundEmail(
            to="cto@example.com",
            subject="ESSEMVEE test",
            body="Controlled test",
            intended_recipient="cto@example.com",
        )
    )

    assert result.delivered_to == "cto@example.com"
    assert result.intended_recipient == "cto@example.com"
    assert result.mode == "production"
    assert result.message_id.startswith("graph-send-")
    assert opener.requests[0].full_url.endswith("/users/info%40essemvee.com/sendMail")
    assert opener.requests[0].get_header("Authorization") == "Bearer test-token"

    payload = json.loads(opener.requests[0].data.decode("utf-8"))
    assert payload["saveToSentItems"] is True
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == "cto@example.com"


def test_list_inbox_messages_maps_reply_fields():
    opener = FakeOpener()
    mailbox = make_mailbox(opener)
    messages = mailbox.list_inbox_messages(top=10)

    assert len(messages) == 1
    assert messages[0].message_id == "graph-message-1"
    assert messages[0].thread_id == "conversation-1"
    assert messages[0].sender == "cto@example.com"
    assert messages[0].body_text == "Interested."


def test_get_message_maps_single_reply():
    opener = FakeOpener()
    mailbox = make_mailbox(opener)
    message = mailbox.get_message("graph-message-1")

    assert message.subject == "Re: ESSEMVEE"
    assert message.internet_message_id == "<internet-1>"
    assert message.thread_id == "conversation-1"


def test_missing_token_is_rejected():
    try:
        OutlookGraphMailbox("info@essemvee.com", access_token="")
    except ValueError as exc:
        assert "MICROSOFT_GRAPH_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected missing-token validation")


def run_all() -> None:
    tests = [
        test_send_uses_configured_mailbox_and_preserves_intended_recipient,
        test_list_inbox_messages_maps_reply_fields,
        test_get_message_maps_single_reply,
        test_missing_token_is_rejected,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("ALL OUTLOOK GRAPH MAILBOX TESTS PASSED")


if __name__ == "__main__":
    run_all()
