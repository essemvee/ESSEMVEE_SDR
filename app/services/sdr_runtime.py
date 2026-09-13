"""Runtime wiring for the ESSEMVEE SDR execution engine.

This module is intentionally lazy: importing the API never creates a real
Microsoft Graph provider or requires a Graph token. The provider is created
only when an execution path explicitly asks for the runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.services.sdr_execution_state import SDRExecutionState
from app.services.sdr_mail_provider import build_mail_provider
from app.services.sdr_orchestrator import SDROrchestrator


@dataclass
class SDRRuntime:
    state: SDRExecutionState
    orchestrator: SDROrchestrator
    provider: object


def build_sdr_runtime() -> SDRRuntime:
    """Build the state store, orchestrator and selected mail provider."""
    mode = os.getenv("SDR_MODE", "test").strip().lower()
    test_recipient = os.getenv("SDR_TEST_RECIPIENT", "viquar1.08@gmail.com")
    mailbox = os.getenv("SDR_MAILBOX")
    db_path = os.getenv("SDR_DB_PATH", "data/sdr_state.sqlite3")

    state = SDRExecutionState(db_path)
    orchestrator = SDROrchestrator(
        state,
        mode=mode,
        test_recipient=test_recipient,
    )
    provider = build_mail_provider(
        mode=mode,
        test_recipient=test_recipient,
        mailbox=mailbox,
    )
    return SDRRuntime(
        state=state,
        orchestrator=orchestrator,
        provider=provider,
    )


__all__ = ["SDRRuntime", "build_sdr_runtime"]
