"""Client reminder app that polls the server and displays due reminder popups."""

from __future__ import annotations

import platform
import queue
import threading
import time
import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk

import requests

from shared.config import POLL_INTERVAL_SECONDS, SERVER_BASE_URL

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:  # noqa: BLE001
    pystray = None
    Image = None
    ImageDraw = None


class ReminderClient:
    def __init__(self) -> None:
        self.user_id: int | None = None
        self.machine_name = platform.node().upper()
        self.stop_event = threading.Event()

        self.popup_queue: queue.Queue[dict] = queue.Queue()
        self.active_popup_reminder: tuple[int, str] | None = None
        self.shown_instances: set[tuple[int, str]] = set()

        self.root = tk.Tk()
        self.root.title("Reminder Client")
        self.root.withdraw()  # Keep app hidden; UI appears only for popups.

    def start(self) -> None:
        self.resolve_user_id()

        polling_thread = threading.Thread(target=self.poll_loop, daemon=True)
        polling_thread.start()

        if pystray:
            tray_thread = threading.Thread(target=self.run_tray, daemon=True)
            tray_thread.start()

        self.root.after(500, self.check_popup_queue)
        self.root.mainloop()

    def resolve_user_id(self) -> None:
        response = requests.get(f"{SERVER_BASE_URL}/users", timeout=5)
        response.raise_for_status()
        users = response.json()

        # Match by computer_name first; fallback to first user for local demos.
        for user in users:
            if user["computer_name"].upper() == self.machine_name:
                self.user_id = int(user["id"])
                break
        if self.user_id is None and users:
            self.user_id = int(users[0]["id"])

        if self.user_id is None:
            raise RuntimeError("No users available on the server")

    def poll_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                response = requests.get(f"{SERVER_BASE_URL}/reminders/{self.user_id}", timeout=6)
                response.raise_for_status()
                reminders = response.json()

                for reminder in reminders:
                    key = (int(reminder["reminder_id"]), reminder["due_at"])
                    if key not in self.shown_instances:
                        self.shown_instances.add(key)
                        self.popup_queue.put(reminder)
            except Exception as exc:  # noqa: BLE001
                print(f"Polling error: {exc}")

            time.sleep(POLL_INTERVAL_SECONDS)

    def check_popup_queue(self) -> None:
        if self.active_popup_reminder is None and not self.popup_queue.empty():
            reminder = self.popup_queue.get()
            self.show_popup(reminder)
        self.root.after(500, self.check_popup_queue)

    def show_popup(self, reminder: dict) -> None:
        reminder_key = (int(reminder["reminder_id"]), reminder["due_at"])
        self.active_popup_reminder = reminder_key

        popup = tk.Toplevel(self.root)
        popup.title("Reminder")
        popup.attributes("-topmost", True)
        popup.geometry("420x220")
        popup.protocol("WM_DELETE_WINDOW", lambda: None)  # force explicit action

        ttk.Label(popup, text="🔔 Reminder Due", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(popup, text=reminder["message"], wraplength=380).pack(pady=10)

        self.play_alert_sound()

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Done",
            command=lambda: self.handle_done(reminder, popup),
        ).grid(row=0, column=0, padx=8)

        for idx, minutes in enumerate((5, 10, 15), start=1):
            ttk.Button(
                button_frame,
                text=f"Snooze {minutes}m",
                command=lambda m=minutes: self.handle_snooze(reminder, popup, m),
            ).grid(row=0, column=idx, padx=8)

    def play_alert_sound(self) -> None:
        # Cross-platform basic alert sound using Tk bell.
        self.root.bell()

    def handle_done(self, reminder: dict, popup: tk.Toplevel) -> None:
        self.send_status_update(reminder_id=int(reminder["reminder_id"]), action="done")
        popup.destroy()
        self.active_popup_reminder = None

    def handle_snooze(self, reminder: dict, popup: tk.Toplevel, minutes: int) -> None:
        self.send_status_update(
            reminder_id=int(reminder["reminder_id"]),
            action="snooze",
            snooze_minutes=minutes,
        )
        popup.destroy()
        self.active_popup_reminder = None

    def send_status_update(self, reminder_id: int, action: str, snooze_minutes: int | None = None) -> None:
        payload = {
            "reminder_id": reminder_id,
            "user_id": self.user_id,
            "action": action,
            "snooze_minutes": snooze_minutes,
        }
        response = requests.post(f"{SERVER_BASE_URL}/reminders/update_status", json=payload, timeout=6)
        response.raise_for_status()

    def run_tray(self) -> None:
        if not pystray or not Image or not ImageDraw:
            return

        def on_quit(icon, _item) -> None:  # noqa: ANN001
            self.stop_event.set()
            icon.stop()
            self.root.after(100, self.root.destroy)

        image = Image.new("RGB", (64, 64), color="black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 56, 56), fill="orange")
        draw.text((18, 21), "R", fill="black")

        menu = (pystray.MenuItem("Quit", on_quit),)
        icon = pystray.Icon("reminder_client", image, "Reminder Client", menu)
        icon.run()


if __name__ == "__main__":
    client = ReminderClient()
    try:
        client.start()
    except Exception as exc:  # noqa: BLE001
        print(f"Fatal client error: {exc}")
