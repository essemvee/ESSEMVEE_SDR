import pytest

from app.services.outlook_graph_mailbox import OutlookGraphMailbox
from app.services.sdr_mail_provider import TestSDRMailProvider, build_mail_provider
from app.services.sdr_mailbox import MailboxConfigurationError


def test_test_mode_never_constructs_graph_provider(monkeypatch):
    monkeypatch.delenv("MICROSOFT_GRAPH_ACCESS_TOKEN", raising=False)
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
