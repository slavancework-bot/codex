"""Admin desktop app to create reminders and inspect active statuses."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, timezone
from tkinter import messagebox, ttk

import requests

from shared.config import SERVER_BASE_URL


class AdminApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Reminder Admin")
        self.geometry("900x600")

        self.users: list[dict] = []

        self._build_form()
        self._build_status_table()
        self.load_users()
        self.refresh_statuses()

    def _build_form(self) -> None:
        frame = ttk.LabelFrame(self, text="Create Reminder")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Message:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.message_text = tk.Text(frame, height=3, width=60)
        self.message_text.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame, text="Date/Time (YYYY-MM-DD HH:MM):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.datetime_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        ttk.Entry(frame, textvariable=self.datetime_var, width=22).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Repeat:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.repeat_var = tk.StringVar(value="one_time")
        ttk.Combobox(
            frame,
            textvariable=self.repeat_var,
            values=["one_time", "weekly"],
            state="readonly",
            width=12,
        ).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Users:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.users_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        self.users_listbox.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(frame, text="Send Reminder", command=self.create_reminder).grid(
            row=2, column=3, sticky="e", padx=5, pady=5
        )

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _build_status_table(self) -> None:
        frame = ttk.LabelFrame(self, text="Active Reminder Statuses")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "user_name", "message", "repeat_type", "status", "snooze_until")
        self.table = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="w")
        self.table.column("message", width=320)
        self.table.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(frame, text="Refresh", command=self.refresh_statuses).pack(anchor="e", padx=5, pady=5)

    def load_users(self) -> None:
        try:
            response = requests.get(f"{SERVER_BASE_URL}/users", timeout=5)
            response.raise_for_status()
            self.users = response.json()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load users failed", str(exc))
            return

        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            self.users_listbox.insert(tk.END, f"{user['id']}: {user['name']} ({user['computer_name']})")

    def selected_user_ids(self) -> list[int]:
        selections = self.users_listbox.curselection()
        return [self.users[idx]["id"] for idx in selections]

    def create_reminder(self) -> None:
        message = self.message_text.get("1.0", tk.END).strip()
        repeat_type = self.repeat_var.get()
        user_ids = self.selected_user_ids()

        if not message:
            messagebox.showwarning("Validation", "Message is required")
            return
        if not user_ids:
            messagebox.showwarning("Validation", "Select at least one user")
            return

        try:
            dt = datetime.strptime(self.datetime_var.get().strip(), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            messagebox.showwarning("Validation", "Invalid datetime format")
            return

        payload = {
            "message": message,
            "scheduled_time": dt.isoformat(),
            "created_by": "admin_app",
            "repeat_type": repeat_type,
            "day_of_week": dt.weekday() if repeat_type == "weekly" else None,
            "user_ids": user_ids,
        }

        try:
            response = requests.post(f"{SERVER_BASE_URL}/reminders/create", json=payload, timeout=7)
            response.raise_for_status()
            messagebox.showinfo("Success", f"Created reminder #{response.json()['reminder_id']}")
            self.message_text.delete("1.0", tk.END)
            self.refresh_statuses()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Create failed", str(exc))

    def refresh_statuses(self) -> None:
        for row_id in self.table.get_children():
            self.table.delete(row_id)

        try:
            response = requests.get(f"{SERVER_BASE_URL}/reminders/active", timeout=5)
            response.raise_for_status()
            rows = response.json()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load statuses failed", str(exc))
            return

        for row in rows:
            self.table.insert(
                "",
                tk.END,
                values=(
                    row["id"],
                    row["user_name"],
                    row["message"],
                    row["repeat_type"],
                    row["status"],
                    row["snooze_until"] or "",
                ),
            )


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
