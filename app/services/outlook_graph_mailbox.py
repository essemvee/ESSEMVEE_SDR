"""Microsoft Graph mailbox adapter for the ESSEMVEE SDR.

This module is the real-provider boundary for Outlook/Microsoft 365. The SDR
orchestrator owns TEST/PRODUCTION recipient isolation; this adapter only sends
or reads the recipient it is explicitly given.

The adapter uses the same provider contract consumed by SDROrchestrator:
``send(to=..., subject=..., body=..., thread_id=...)`` returning the
orchestrator SendResult. Messages are created as drafts before sending so the
actual Microsoft Graph message ID and conversation ID can be persisted even
though Graph's send operation itself returns 202 with no response body.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.sdr_mailbox import MailboxConfigurationError


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


class OutlookGraphMailbox:
    """Microsoft Graph implementation of the SDR MailProvider contract."""

    mode = "production"
    provider_name = "outlook_graph"

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

    def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ):
        """Send a new message or a reply using the SDR MailProvider contract.

        TEST-mode recipient redirection is deliberately not implemented here;
        SDROrchestrator must pass the already-isolated actual recipient.
        """
        if not to or "@" not in to:
            raise MailboxConfigurationError("A valid outbound recipient is required")
        if not subject.strip():
            raise MailboxConfigurationError("Email subject cannot be empty")
        if not body.strip():
            raise MailboxConfigurationError("Email body cannot be empty")

        if thread_id:
            _, draft, _ = self._request(
                "POST",
                f"users/{quote(self.mailbox, safe='')}/messages/{quote(thread_id, safe='')}/createReply",
                payload={"comment": body},
                expected_status=(201,),
            )
        else:
            _, draft, _ = self._request(
                "POST",
                f"users/{quote(self.mailbox, safe='')}/messages",
                payload={
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": to}}],
                },
                expected_status=(201,),
            )

        draft = draft or {}
        message_id = str(draft.get("id", ""))
        if not message_id:
            raise GraphMailboxError("Microsoft Graph did not return a draft message ID")

        conversation_id = draft.get("conversationId") or thread_id
        self._request(
            "POST",
            f"users/{quote(self.mailbox, safe='')}/messages/{quote(message_id, safe='')}/send",
            expected_status=(202,),
        )

        from app.services.sdr_orchestrator import SendResult

        return SendResult(
            message_id=message_id,
            thread_id=conversation_id,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            provider=self.provider_name,
        )

    def reply(self, message_id: str, text_content: str):
        """Compatibility helper for direct Outlook replies."""
        if not message_id:
            raise MailboxConfigurationError("An Outlook message ID is required")
        if not text_content.strip():
            raise MailboxConfigurationError("Reply text cannot be empty")
        return self.send(
            to=self.mailbox,
            subject="Re:",
            body=text_content,
            thread_id=message_id,
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


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "GRAPH_BASE_URL",
    "GraphMailboxError",
    "GraphMessage",
    "OutlookGraphMailbox",
]
