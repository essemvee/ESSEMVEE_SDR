"""Microsoft Graph mailbox adapter for the ESSEMVEE SDR.

This module contains the real-provider boundary for Outlook/Microsoft 365.
It does not contain credentials. A caller supplies an OAuth access token
through a token provider and explicitly supplies the mailbox address.

The adapter supports:
- sending new messages from a specific mailbox;
- replying to an existing Outlook message/thread;
- listing recent inbox messages for a mailbox;
- returning provider message identifiers needed by the SDR state engine.

TEST safety is handled outside this adapter by SDROrchestrator. This adapter
never silently redirects production mail and never invents credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.sdr_mailbox import (
    MailboxConfigurationError,
    MailboxProvider,
    OutboundEmail,
)


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class GraphMessage:
    message_id: str
    thread_id: str | None
    internet_message_id: str | None
    subject: str | None
    sender: str | None
    received_at: str | None
    body_text: str | None


class GraphMailboxError(RuntimeError):
    """Raised when Microsoft Graph rejects or cannot complete an operation."""


class OutlookGraphMailbox(MailboxProvider):
    """Microsoft Graph implementation of the SDR mailbox contract.

    The access token is supplied either explicitly or through the
    ``MICROSOFT_GRAPH_ACCESS_TOKEN`` environment variable. The mailbox must
    be supplied explicitly; ``info@essemvee.com`` is the intended production
    mailbox for this project but is not silently assumed by the adapter.
    """

    mode = "production"

    def __init__(
        self,
        mailbox: str,
        *,
        access_token: str | None = None,
        graph_base_url: str = GRAPH_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self.mailbox = mailbox.strip().lower()
        if not self.mailbox or "@" not in self.mailbox:
            raise MailboxConfigurationError("A valid Microsoft 365 mailbox is required")

        token = access_token or os.getenv("MICROSOFT_GRAPH_ACCESS_TOKEN")
        if not token:
            raise MailboxConfigurationError(
                "MICROSOFT_GRAPH_ACCESS_TOKEN is required for the Outlook Graph adapter"
            )

        self.access_token = token
        self.graph_base_url = graph_base_url.rstrip("/")
        self.timeout = timeout
        self._opener = opener or urlopen

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> tuple[int, dict | None, Mapping[str, str]]:
        url = f"{self.graph_base_url}/{path.lstrip('/')}"
        data = None
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method.upper())
        try:
            response = self._opener(request, timeout=self.timeout)
            status = getattr(response, "status", None) or response.getcode()
            raw = response.read()
            response_headers = dict(getattr(response, "headers", {}) or {})
        except HTTPError as exc:
            raw = exc.read()
            detail = raw.decode("utf-8", errors="replace")
            raise GraphMailboxError(
                f"Microsoft Graph HTTP {exc.code}: {detail[:1000]}"
            ) from exc
        except URLError as exc:
            raise GraphMailboxError(f"Microsoft Graph connection failed: {exc}") from exc
        except OSError as exc:
            raise GraphMailboxError(f"Microsoft Graph request failed: {exc}") from exc

        if status not in expected_status:
            detail = raw.decode("utf-8", errors="replace")
            raise GraphMailboxError(f"Microsoft Graph HTTP {status}: {detail[:1000]}")

        if not raw:
            return status, None, response_headers
        try:
            return status, json.loads(raw.decode("utf-8")), response_headers
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GraphMailboxError("Microsoft Graph returned invalid JSON") from exc

    def send(self, email: OutboundEmail):
        """Send a new message from the configured mailbox."""
        if not email.to or "@" not in email.to:
            raise MailboxConfigurationError("A valid outbound recipient is required")
        if not email.intended_recipient:
            raise MailboxConfigurationError("The intended recipient must be preserved")

        payload = {
            "message": {
                "subject": email.subject,
                "body": {"contentType": "Text", "content": email.body},
                "toRecipients": [{"emailAddress": {"address": email.to}}],
            },
            "saveToSentItems": True,
        }
        self._request(
            "POST",
            f"users/{quote(self.mailbox, safe='')}/sendMail",
            payload=payload,
            expected_status=(202,),
        )

        # Graph sendMail normally returns 202 with no message ID. The caller
        # therefore records a deterministic local send token and should use
        # inbox polling to correlate the provider message when required.
        import uuid

        return _send_result(
            message_id=f"graph-send-{uuid.uuid4().hex}",
            thread_id=None,
            delivered_to=email.to,
            intended_recipient=email.intended_recipient,
            mode=self.mode,
        )

    def reply(self, message_id: str, text_content: str):
        """Reply to an existing message using Microsoft Graph."""
        if not message_id:
            raise MailboxConfigurationError("An Outlook message ID is required")
        if not text_content.strip():
            raise MailboxConfigurationError("Reply text cannot be empty")

        self._request(
            "POST",
            f"users/{quote(self.mailbox, safe='')}/messages/{quote(message_id, safe='')}/reply",
            payload={"comment": text_content},
            expected_status=(202,),
        )

    def list_inbox_messages(self, *, top: int = 25) -> list[GraphMessage]:
        """Fetch recent inbox messages for reply monitoring."""
        if top < 1 or top > 100:
            raise ValueError("top must be between 1 and 100")

        path = (
            f"users/{quote(self.mailbox, safe='')}/mailFolders/inbox/messages"
            f"?$top={top}&$orderby=receivedDateTime%20desc"
            "&$select=id,conversationId,internetMessageId,subject,from,receivedDateTime,body"
        )
        _, payload, _ = self._request("GET", path)
        values = (payload or {}).get("value", [])
        return [_map_message(item) for item in values if isinstance(item, dict)]

    def get_message(self, message_id: str) -> GraphMessage:
        """Fetch one Outlook message by provider message ID."""
        if not message_id:
            raise MailboxConfigurationError("An Outlook message ID is required")
        path = (
            f"users/{quote(self.mailbox, safe='')}/messages/{quote(message_id, safe='')}"
            "?$select=id,conversationId,internetMessageId,subject,from,receivedDateTime,body"
        )
        _, payload, _ = self._request("GET", path)
        if not payload:
            raise GraphMailboxError("Microsoft Graph returned an empty message")
        return _map_message(payload)


def _map_message(item: dict) -> GraphMessage:
    sender = ((item.get("from") or {}).get("emailAddress") or {}).get("address")
    body = item.get("body") or {}
    body_text = body.get("content") if isinstance(body, dict) else None
    return GraphMessage(
        message_id=str(item.get("id", "")),
        thread_id=item.get("conversationId"),
        internet_message_id=item.get("internetMessageId"),
        subject=item.get("subject"),
        sender=sender,
        received_at=item.get("receivedDateTime"),
        body_text=body_text,
    )


def _send_result(*, message_id: str, thread_id: str | None, delivered_to: str,
                 intended_recipient: str, mode: str):
    """Create the project's SendResult without duplicating mailbox models."""
    from app.services.sdr_mailbox import SendResult

    return SendResult(
        message_id=message_id,
        thread_id=thread_id or "",
        delivered_to=delivered_to,
        intended_recipient=intended_recipient,
        mode=mode,
    )


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "GRAPH_BASE_URL",
    "GraphMailboxError",
    "GraphMessage",
    "OutlookGraphMailbox",
]
