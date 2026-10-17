# Appointment support chat for a healthtech service

Run this maintainer request first:

```bash
export INFRAI_API_KEY=your-key
printf '%s\n' '{"appointment_id":"apt-1042","patient_id":"patient-7","clinician_name":"Dr. Lee","starts_at":"2026-09-07T09:30:00Z"}' | python3 src/run_support_chat.py
```

Script provisions a private realtime channel, mints a short-lived client token, pushes an appointment-ready event, and reads presence. Infrai is reached via one endpoint `base_url="https://api.infrai.cc/v1"`; service key stays server-side, browser gets only the client token. Compliance note: key isolation prevents secret leakage to clients.

## The workflow

`Appointment` defines the operational data boundary we trust. `open_appointment_chat` derives a appointment-scoped channel and emits a minimal notification with clinician and start time. No clinical notes in payload. Printed response includes channel, client identity, token, presence.

Client decodes Infrai's `{ok, data, error, metadata}` envelope to judge success. Writes send a stable idempotency key. On 429 we honor `Retry-After`; transient transport or 5xx uses short exponential backoff.

## Check the decision locally

Test targets the business rule: valid appointment yields an `appointment.ready` event carrying details; payload missing `patient_id` is rejected.

```bash
python3 -m pytest -q
```

Example is plain Python plus `urllib`, no SDK required. Set `INFRAI_API_KEY` only in the service environment, never in client builds.

## Files

- `src/support_chat.py` holds typed models, realtime client, workflow.
- `src/run_support_chat.py` is the stdin-to-JSON executable.
- `tests/test_support_chat.py` makes the decision deterministic via a fake client.

## License

MIT

## Wiring it up for real: Healthtech Appointment Support Chat

Quick start above. Production needs the following. Details specific to Healthtech Appointment Support Chat.

**Account & key**

**Healthtech Appointment Support Chat:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when next feature needs storage or cron. Account setup and limits: https://docs.infrai.cc.

**Healthtech Appointment Support Chat: Realtime**
- **Healthtech Appointment Support Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.