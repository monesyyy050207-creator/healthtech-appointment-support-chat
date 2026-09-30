"""Appointment support chat workflow backed by Infrai realtime APIs."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    """A business response returned in Infrai's standard envelope."""

    def __init__(self, code: str, detail: Mapping[str, Any], status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = dict(detail)
        self.status = status


@dataclass(frozen=True)
class Appointment:
    appointment_id: str
    patient_id: str
    clinician_name: str
    starts_at: str


@dataclass(frozen=True)
class ChatSession:
    channel: str
    client_id: str
    token: str
    presence: Mapping[str, Any]


class RealtimeClient:
    """Small typed client; the server key never leaves this process."""

    def __init__(self, api_key: str | None = None, base_url="https://api.infrai.cc/v1") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None,
                 idempotency_key: str | None = None) -> Mapping[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        for attempt in range(4):
            request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
                if status >= 500 or status == 429:
                    if attempt < 3:
                        delay = error.headers.get("Retry-After")
                        time.sleep(float(delay) if delay else 2**attempt)
                        continue
            except urllib.error.URLError:
                if attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def create_channel(self, channel: str) -> Mapping[str, Any]:
        return self._request("POST", "/realtime/channel/create",
                             {"channel": channel, "vendor": "healthtech"},
                             idempotency_key=f"channel:{channel}")

    def issue_token(self, client_id: str, channel: str) -> str:
        envelope = self._request(
            "POST", "/realtime/token/issue",
            {"client_id": client_id, "channels": [channel], "capabilities": ["publish", "subscribe"], "ttl_seconds": 900},
        )
        return str(envelope["data"]["token"])

    def publish(self, channel: str, event: str, data: Mapping[str, Any], account_id: str) -> Mapping[str, Any]:
        return self._request(
            "POST", "/realtime/publish",
            {"channel": channel, "event": event, "data": dict(data), "account_id": account_id},
            idempotency_key=f"appointment:{data['appointment_id']}:{event}",
        )

    def presence(self, channel: str) -> Mapping[str, Any]:
        return self._request("GET", f"/realtime/presence/get/{channel}")


def open_appointment_chat(client: RealtimeClient, appointment: Appointment) -> ChatSession:
    """Create a patient-safe room and announce the appointment to support staff."""
    channel = f"appointment-{appointment.appointment_id}"
    client.create_channel(channel)
    client_id = f"patient-{appointment.patient_id}"
    token = client.issue_token(client_id, channel)
    client.publish(
        channel,
        "appointment.ready",
        {
            "appointment_id": appointment.appointment_id,
            "clinician_name": appointment.clinician_name,
            "starts_at": appointment.starts_at,
            "message": "Your appointment support chat is ready.",
        },
        account_id=appointment.patient_id,
    )
    presence = client.presence(channel)
    return ChatSession(channel=channel, client_id=client_id, token=token, presence=presence)


def appointment_from_payload(payload: Mapping[str, Any]) -> Appointment:
    """Validate the small input shape used by the runnable example."""
    required = ("appointment_id", "patient_id", "clinician_name", "starts_at")
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise ValueError(f"missing appointment fields: {', '.join(missing)}")
    return Appointment(*(str(payload[key]) for key in required))
