"""FastAPI reminder server with SQLite-backed storage."""

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException

from server.database import get_conn, init_db
from server.schemas import ReminderCreateRequest, ReminderDue, ReminderStatusUpdateRequest, UserOut

app = FastAPI(title="Reminder Server")


def iso_utc_now() -> str:
    """Return current UTC timestamp as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_iso(dt_str: str) -> datetime:
    """Parse stored ISO string to timezone-aware datetime (UTC if naive)."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def next_weekly_due(base: datetime, now: datetime) -> datetime:
    """Compute the due time for a weekly reminder in relation to now."""
    due = base
    while due <= now:
        due += timedelta(days=7)
    return due


@app.on_event("startup")
def startup() -> None:
    """Initialize DB tables when server starts."""
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/users", response_model=list[UserOut])
def list_users() -> list[UserOut]:
    """List users for admin assignment UI."""
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, computer_name FROM users ORDER BY name").fetchall()
    return [UserOut(**dict(r)) for r in rows]


@app.post("/reminders/create")
def create_reminder(payload: ReminderCreateRequest) -> dict[str, int]:
    """Create a reminder and assign it to selected users."""
    if payload.repeat_type == "weekly" and payload.day_of_week is None:
        raise HTTPException(status_code=400, detail="day_of_week is required for weekly reminders")

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO reminders(message, scheduled_time, created_by, repeat_type, day_of_week)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.message,
                payload.scheduled_time.astimezone(timezone.utc).isoformat(),
                payload.created_by,
                payload.repeat_type,
                payload.day_of_week,
            ),
        )
        reminder_id = cur.lastrowid

        for user_id in payload.user_ids:
            exists = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
            conn.execute(
                "INSERT INTO assignments(reminder_id, user_id, status) VALUES (?, ?, 'pending')",
                (reminder_id, user_id),
            )

    return {"reminder_id": int(reminder_id)}


@app.get("/reminders/{user_id}", response_model=list[ReminderDue])
def get_due_reminders(user_id: int) -> list[ReminderDue]:
    """Return active/due reminders for one user.

    Active reminders are pending or snoozed rows not marked completed.
    """
    now = datetime.now(timezone.utc)

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id AS assignment_id,
                a.user_id,
                a.status,
                a.snooze_until,
                r.id AS reminder_id,
                r.message,
                r.repeat_type,
                r.scheduled_time
            FROM assignments a
            JOIN reminders r ON r.id = a.reminder_id
            WHERE a.user_id = ?
              AND a.status IN ('pending', 'snoozed')
            ORDER BY r.scheduled_time
            """,
            (user_id,),
        ).fetchall()

    due: list[ReminderDue] = []
    for row in rows:
        scheduled = parse_iso(row["scheduled_time"])
        due_at = parse_iso(row["snooze_until"]) if row["snooze_until"] else scheduled

        # Weekly reminders recur every 7 days after the original schedule.
        if row["repeat_type"] == "weekly" and not row["snooze_until"]:
            while due_at + timedelta(days=7) <= now:
                due_at += timedelta(days=7)

        if due_at <= now:
            due.append(
                ReminderDue(
                    reminder_id=row["reminder_id"],
                    assignment_id=row["assignment_id"],
                    message=row["message"],
                    repeat_type=row["repeat_type"],
                    scheduled_time=scheduled.isoformat(),
                    due_at=due_at.isoformat(),
                )
            )

    return due


@app.post("/reminders/update_status")
def update_status(payload: ReminderStatusUpdateRequest) -> dict[str, str]:
    """Update one reminder status for one user (done or snooze)."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT a.id AS assignment_id, a.status, r.repeat_type, r.scheduled_time
            FROM assignments a
            JOIN reminders r ON r.id = a.reminder_id
            WHERE a.reminder_id = ? AND a.user_id = ?
            """,
            (payload.reminder_id, payload.user_id),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")

        now = datetime.now(timezone.utc)

        if payload.action == "snooze":
            if not payload.snooze_minutes:
                raise HTTPException(status_code=400, detail="snooze_minutes is required for snooze")
            snooze_until = now + timedelta(minutes=payload.snooze_minutes)
            conn.execute(
                """
                UPDATE assignments
                SET status = 'snoozed', snooze_until = ?, completed_time = NULL
                WHERE reminder_id = ? AND user_id = ?
                """,
                (snooze_until.isoformat(), payload.reminder_id, payload.user_id),
            )
            return {"status": "snoozed"}

        # Done action
        if row["repeat_type"] == "weekly":
            # Reset to pending and clear snooze so it can appear next week.
            conn.execute(
                """
                UPDATE assignments
                SET status = 'pending', snooze_until = NULL, completed_time = ?
                WHERE reminder_id = ? AND user_id = ?
                """,
                (now.isoformat(), payload.reminder_id, payload.user_id),
            )
            return {"status": "completed_weekly_occurrence"}

        conn.execute(
            """
            UPDATE assignments
            SET status = 'completed', completed_time = ?, snooze_until = NULL
            WHERE reminder_id = ? AND user_id = ?
            """,
            (now.isoformat(), payload.reminder_id, payload.user_id),
        )

    return {"status": "completed"}


@app.get("/reminders/active")
def list_active_assignments() -> list[dict]:
    """Admin helper endpoint to show active reminder assignment statuses."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
              a.id,
              u.name AS user_name,
              r.message,
              r.repeat_type,
              a.status,
              a.snooze_until,
              a.completed_time
            FROM assignments a
            JOIN reminders r ON r.id = a.reminder_id
            JOIN users u ON u.id = a.user_id
            WHERE a.status IN ('pending', 'snoozed')
            ORDER BY a.id DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]
