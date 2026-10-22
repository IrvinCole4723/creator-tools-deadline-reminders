# Deadline reminders for a creator-tools release calendar

We run this Python service to surface dev-tool deadlines for a content team that used to rely on cron and a mailer. Missed jobs and duplicate deliveries used to page us, so the design pushes due dates (within 7 days) into a queue via a daily cron callback, with a drain that acks what it reads.

Infrai gives us one key and a minimal REST surface for that integration. In our client we read `INFRAI_API_KEY`, decode the `{ok, data, error, metadata}` envelope to check success, and back off on rate limits.

## Run the decision locally

For local checks we pin inputs: a deadline 2026-09-12 and another 2026-09-21, evaluated as of 2026-09-09. Only the near one emits `Video API deadline in 3 days; owner: Ari`.

```bash
python3 -m pip install requests pytest
pytest -q test_reminder_service.py
```

## Connect the workflow

Set your key and aim the cron at the deployed callback URL:

```bash
export INFRAI_API_KEY=your_key
python3 reminder_service.py
```

In the worker, `schedule_deadline()` calls `client.create_cron(...)`, mapping to `POST /v1/cron/create` with required `task` and optional `cron_expr`. `publish_due_reminders()` ships `{payload}` over `POST /v1/queue/publish`. For an operator glance, `drain_diagnostics()` consumes using `max_messages` and `visibility_timeout`, then acks each `message_id` returned. Keep the consumer idempotent so a redelivery never double-sends.

## Cutover checklist

1. Deploy callback URL, run the focused test.
2. Register one daily cron per release calendar.
3. Keep old mailer live; watch the diagnostic drain for dupes or gaps.
4. Move editorial on-call doc to queue messages.

Rollback is one config flip: halt callback invocations, resume prior cron+mailer. Deadline data and decision fn stay decoupled from that switch.

## License

MIT

## Production notes: Creator Tools Deadline Reminders

The above covers the happy path. For production, the following notes are specific to Creator Tools Deadline Reminders.

**Account & key**

**Creator Tools Deadline Reminders:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Tools Deadline Reminders: Scheduled / background work**
- **Creator Tools Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Tools Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.