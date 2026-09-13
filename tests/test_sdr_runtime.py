from app.services.sdr_mail_provider import TestSDRMailProvider
from app.services.sdr_runtime import build_sdr_runtime


def test_runtime_defaults_to_test_provider(monkeypatch, tmp_path):
    monkeypatch.delenv("SDR_MODE", raising=False)
    monkeypatch.delenv("SDR_MAILBOX", raising=False)
    monkeypatch.delenv("MICROSOFT_GRAPH_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("SDR_DB_PATH", str(tmp_path / "sdr.sqlite3"))

    runtime = build_sdr_runtime()
    try:
        assert runtime.orchestrator.mode == "test"
        assert isinstance(runtime.provider, TestSDRMailProvider)
        assert runtime.provider.test_recipient == "viquar1.08@gmail.com"
    finally:
        runtime.state.close()
