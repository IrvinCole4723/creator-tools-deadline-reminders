from dataclasses import dataclass
from datetime import date

from infrai_client import InfraiClient


@dataclass(frozen=True)
class Deadline:
    tool: str
    deadline: date
    owner: str


def reminder_for(deadline: Deadline, today: date, horizon_days: int = 7) -> str | None:
    days_left = (deadline.deadline - today).days
    if 0 <= days_left <= horizon_days:
        return f"{deadline.tool} deadline in {days_left} days; owner: {deadline.owner}"
    return None


def schedule_deadline(client: InfraiClient, deadline: Deadline, callback_url: str) -> str:
    job = client.create_cron("0 9 * * *", callback_url)
    return str(job["job_id"])


def publish_due_reminders(client: InfraiClient, deadlines: list[Deadline], today: date) -> list[str]:
    sent: list[str] = []
    for deadline in deadlines:
        message = reminder_for(deadline, today)
        if message:
            client.publish({"text": message, "tool": deadline.tool, "owner": deadline.owner})
            sent.append(message)
    return sent


def drain_diagnostics(client: InfraiClient) -> list[dict]:
    result = client.consume(max_messages=20, visibility_timeout=60)
    messages = result.get("messages") or []
    for message in messages:
        client.ack(message["message_id"])
    return messages


if __name__ == "__main__":
    client = InfraiClient()
    item = Deadline("Creator CLI", date.today(), "Mina")
    print(publish_due_reminders(client, [item], date.today()))
