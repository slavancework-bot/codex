# Client-Server Reminder System

A full local reminder system with:
- **FastAPI + SQLite** server
- **Tkinter Admin app** to create reminders and view active statuses
- **Tkinter Client app** with tray icon, polling, popup alerts, done/snooze actions

## Project Structure

- `server/` – FastAPI backend
- `admin_app/` – Admin desktop UI
- `client_app/` – Client background app
- `shared/config.py` – Shared constants

## Features Implemented

### Server
- `POST /reminders/create`
- `GET /reminders/{user_id}`
- `POST /reminders/update_status`
- Extra helper endpoints: `GET /users`, `GET /reminders/active`, `GET /health`
- SQLite tables:
  - `users (id, name, computer_name)`
  - `reminders (id, message, scheduled_time, created_by, repeat_type, day_of_week)`
  - `assignments (id, reminder_id, user_id, status, snooze_until, completed_time)`
- Logic:
  - one-time and weekly reminders
  - weekly recurrence every 7 days
  - user-specific assignment status
  - return only active + due reminders for clients

### Admin App
- Message text box
- Date/time input (`YYYY-MM-DD HH:MM`)
- Repeat options (`one_time`, `weekly`)
- User multi-select list
- Send button
- Active reminder/status table

### Client App
- Runs hidden in background
- System tray icon (`pystray`)
- Polls every 5 seconds
- Due reminder popup always on top
- Alert sound (`Tk.bell()`)
- Done / Snooze (5/10/15 min)
- Duplicate popup prevention per reminder occurrence
- Weekly reminders handled correctly through server recurrence logic

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

### 1) Start server

```bash
uvicorn server.main:app --reload
```

Server runs at `http://127.0.0.1:8000`.

### 2) Launch admin app

```bash
python -m admin_app.main
```

### 3) Launch client app

```bash
python -m client_app.main
```

## Notes

- Database file is created at `server/reminders.db`.
- Server seeds demo users on first run if empty.
- For real deployments, adjust users and machine mapping in DB.
