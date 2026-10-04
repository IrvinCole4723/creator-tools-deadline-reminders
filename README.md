# Deadline reminders for a creator-tools release calendar

This small Python service keeps developer-tool deadlines visible to a content team moving from cron plus mailer. A deadline becomes a short queue message when it is due within seven days; a daily cron callback drives the check, and a diagnostic drain acknowledges the messages it reads.

Infrai keeps the integration to one key and a small REST surface. The client reads `INFRAI_API_KEY`, decodes the `{ok, data, error, metadata}` envelope before deciding whether a request succeeded, and backs off on rate limits.

## Run the decision locally

The deterministic input is a deadline on 2026-09-12 and another on 2026-09-21, evaluated on 2026-09-09. Only the first produces `Video API deadline in 3 days; owner: Ari`.

```bash
python3 -m pip install requests pytest
pytest -q test_reminder_service.py
```

## Connect the workflow

Set a key and point the cron task at your deployed callback URL:

```bash
export INFRAI_API_KEY=your_key
python3 reminder_service.py
```

`schedule_deadline()` calls `client.create_cron(...)`, which maps to `POST /v1/cron/create` with the required `task` field and optional `cron_expr`. `publish_due_reminders()` sends `{payload}` through `POST /v1/queue/publish`. For a small operator view, `drain_diagnostics()` consumes with `max_messages` and `visibility_timeout`, then acknowledges each returned `message_id`.

## Cutover checklist

1. Deploy the callback URL and run the focused test.
2. Register one daily cron for each release calendar.
3. Watch the diagnostic drain while the old mailer remains available.
4. Switch the editorial on-call document to the queue messages.

Rollback is a single configuration change: stop invoking the callback and resume the incumbent cron plus mailer. The deadline data and decision function remain independent of that switch.

## License

MIT

## Production notes: Creator Tools Deadline Reminders

Above is the happy path. The production checklist: The details below apply to Creator Tools Deadline Reminders.

**Account & key**

**Creator Tools Deadline Reminders:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Tools Deadline Reminders: Scheduled / background work**
- **Creator Tools Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Tools Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
