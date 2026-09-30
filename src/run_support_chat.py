import json
import sys

from support_chat import RealtimeClient, appointment_from_payload, open_appointment_chat


def main() -> None:
    raw = sys.stdin.read() or '{"appointment_id":"apt-1042","patient_id":"patient-7","clinician_name":"Dr. Lee","starts_at":"2026-09-07T09:30:00Z"}'
    appointment = appointment_from_payload(json.loads(raw))
    session = open_appointment_chat(RealtimeClient(), appointment)
    print(json.dumps({"channel": session.channel, "client_id": session.client_id, "token": session.token, "presence": session.presence}))


if __name__ == "__main__":
    main()
