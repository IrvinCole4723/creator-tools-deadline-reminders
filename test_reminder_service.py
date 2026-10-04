from datetime import date, timedelta
from unittest.mock import Mock, patch

from infrai_client import InfraiClient
from reminder_service import Deadline, publish_due_reminders, reminder_for


class FakeClient:
    def __init__(self):
        self.payloads = []

    def publish(self, payload):
        self.payloads.append(payload)
        return {}


def test_only_deadlines_within_seven_days_are_published():
    today = date(2026, 9, 9)
    due = Deadline("Video API", today + timedelta(days=3), "Ari")
    later = Deadline("Render API", today + timedelta(days=12), "Bo")
    client = FakeClient()
    sent = publish_due_reminders(client, [due, later], today)
    assert sent == ["Video API deadline in 3 days; owner: Ari"]
    assert client.payloads[0]["tool"] == "Video API"
    assert reminder_for(later, today) is None


def test_rate_limit_error_envelope_is_retried(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    rate_limited = Mock(status_code=429, headers={"Retry-After": "0"})
    rate_limited.json.return_value = {"ok": False, "error": {"code": "RATE_LIMITED"}}
    success = Mock(status_code=200, headers={})
    success.json.return_value = {"ok": True, "data": {"message_id": "msg-1"}}

    with patch("infrai_client.requests.request", side_effect=[rate_limited, success]) as request:
        with patch("infrai_client.time.sleep"):
            result = InfraiClient().publish({"text": "due"})

    assert result == {"message_id": "msg-1"}
    assert request.call_count == 2


def test_server_error_envelope_is_retried(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    unavailable = Mock(status_code=503, headers={})
    unavailable.json.return_value = {"ok": False, "error": {"code": "UNAVAILABLE"}}
    success = Mock(status_code=200, headers={})
    success.json.return_value = {"ok": True, "data": {"message_id": "msg-2"}}

    with patch("infrai_client.requests.request", side_effect=[unavailable, success]) as request:
        with patch("infrai_client.time.sleep"):
            result = InfraiClient().publish({"text": "due"})

    assert result == {"message_id": "msg-2"}
    assert request.call_count == 2
