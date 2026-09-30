import pytest

from src.support_chat import RealtimeClient, appointment_from_payload, open_appointment_chat


class FakeRealtime(RealtimeClient):
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("create", channel))
        return {"ok": True}

    def issue_token(self, client_id, channel):
        self.calls.append(("token", client_id, channel))
        return "client-token"

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"ok": True}

    def presence(self, channel):
        self.calls.append(("presence", channel))
        return {"ok": True, "data": {"members": 1}}


def test_open_chat_announces_only_appointment_details():
    appointment = appointment_from_payload({"appointment_id": "a-1", "patient_id": "p-9", "clinician_name": "Dr. Chen", "starts_at": "2026-09-07T10:00:00Z"})
    fake = FakeRealtime()
    session = open_appointment_chat(fake, appointment)
    assert session.channel == "appointment-a-1"
    publish = next(call for call in fake.calls if call[0] == "publish")
    assert publish[2] == "appointment.ready"
    assert publish[3]["appointment_id"] == "a-1"
    assert "diagnosis" not in publish[3]


def test_payload_requires_patient_identity():
    with pytest.raises(ValueError, match="patient_id"):
        appointment_from_payload({"appointment_id": "a-1", "clinician_name": "Dr. Chen", "starts_at": "2026-09-07T10:00:00Z"})
