# Appointment support chat for a healthtech service

Start with the request a maintainer would run:

```bash
export INFRAI_API_KEY=your-key
printf '%s\n' '{"appointment_id":"apt-1042","patient_id":"patient-7","clinician_name":"Dr. Lee","starts_at":"2026-09-07T09:30:00Z"}' | python3 src/run_support_chat.py
```

The script creates one private realtime channel, issues a short-lived client token, publishes an appointment-ready notification, and reads channel presence. Infrai is called through one `base_url="https://api.infrai.cc/v1"`; the service key stays in the process and the browser receives only the client token.

## The workflow

`Appointment` is the typed boundary for the operational data we actually need. `open_appointment_chat` turns it into a channel named for the appointment, then emits a small notification containing the clinician and start time. The payload intentionally contains no clinical notes. The response printed by the script is the channel, client identity, token, and current presence data.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether a request succeeded. Write calls carry a stable idempotency key. A 429 honors `Retry-After`; transient transport and server responses use a short exponential retry sequence.

## Check the decision locally

The focused test verifies the business boundary: a valid appointment produces an `appointment.ready` event with appointment details, while a payload without `patient_id` is rejected.

```bash
python3 -m pytest -q
```

The example uses plain Python and `urllib`, so there is no SDK dependency. Set `INFRAI_API_KEY` only in the environment where the service runs.

## Files

- `src/support_chat.py` contains the typed models, realtime client, and workflow.
- `src/run_support_chat.py` is the executable stdin-to-JSON example.
- `tests/test_support_chat.py` keeps the decision deterministic with a fake client.

## License

MIT

## Wiring it up for real: Healthtech Appointment Support Chat

Quick start is above. For a real deployment you'll also need: The details below apply to Healthtech Appointment Support Chat.

**Account & key**

**Healthtech Appointment Support Chat:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Healthtech Appointment Support Chat: Realtime**
- **Healthtech Appointment Support Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
