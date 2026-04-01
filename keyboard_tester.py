#!/usr/bin/env python3
"""Linux keyboard tester with a persistent key-press highlight."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

KEY_BG = "#f2f3f5"
KEY_FG = "#1f2937"
PRESSED_BG = "#34d399"
PRESSED_FG = "#0b3d2e"
FRAME_BG = "#d1d5db"
WINDOW_BG = "#e5e7eb"


class KeyboardTester(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Keyboard Tester")
        self.configure(bg=WINDOW_BG)
        self.resizable(False, False)

        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), background=WINDOW_BG)
        style.configure("Hint.TLabel", font=("Segoe UI", 10), background=WINDOW_BG)

        self._buttons_by_id: dict[str, tk.Button] = {}
        self._pressed: set[str] = set()

        self._build_ui()
        self.bind_all("<KeyPress>", self._on_key_press, add="+")
        self.focus_force()

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self, bg=WINDOW_BG, padx=16, pady=16)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(wrapper, text="Press every key to verify it works", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            wrapper,
            text="Keys stay highlighted after the first successful press.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(2, 12))

        keyboard = tk.Frame(wrapper, bg=FRAME_BG, padx=10, pady=10)
        keyboard.pack()

        rows = [
            [
                self.key("Esc", ["Escape"], 2),
                self.key("F1", ["F1"]), self.key("F2", ["F2"]), self.key("F3", ["F3"]), self.key("F4", ["F4"]),
                self.key("F5", ["F5"]), self.key("F6", ["F6"]), self.key("F7", ["F7"]), self.key("F8", ["F8"]),
                self.key("F9", ["F9"]), self.key("F10", ["F10"]), self.key("F11", ["F11"]), self.key("F12", ["F12"]),
                self.key("PrtSc", ["Print"]), self.key("ScrLk", ["Scroll_Lock"]), self.key("Pause", ["Pause"]),
            ],
            [
                self.key("`", ["grave", "asciitilde"]),
                self.key("1", ["1", "exclam"]), self.key("2", ["2", "at"]), self.key("3", ["3", "numbersign"]),
                self.key("4", ["4", "dollar"]), self.key("5", ["5", "percent"]), self.key("6", ["6", "asciicircum"]),
                self.key("7", ["7", "ampersand"]), self.key("8", ["8", "asterisk"]), self.key("9", ["9", "parenleft"]),
                self.key("0", ["0", "parenright"]),
                self.key("-", ["minus", "underscore"]),
                self.key("=", ["equal", "plus"]),
                self.key("Backspace", ["BackSpace"], 3),
                self.key("Ins", ["Insert"]), self.key("Home", ["Home"]), self.key("PgUp", ["Prior"]),
                self.key("Num", ["Num_Lock"]), self.key("/", ["KP_Divide"]), self.key("*", ["KP_Multiply"]), self.key("-", ["KP_Subtract"]),
            ],
            [
                self.key("Tab", ["Tab"], 2),
                self.key("Q", ["q", "Q"]), self.key("W", ["w", "W"]), self.key("E", ["e", "E"]), self.key("R", ["r", "R"]),
                self.key("T", ["t", "T"]), self.key("Y", ["y", "Y"]), self.key("U", ["u", "U"]), self.key("I", ["i", "I"]),
                self.key("O", ["o", "O"]), self.key("P", ["p", "P"]),
                self.key("[", ["bracketleft", "braceleft"]),
                self.key("]", ["bracketright", "braceright"]),
                self.key("\\", ["backslash", "bar"], 2),
                self.key("Del", ["Delete"]), self.key("End", ["End"]), self.key("PgDn", ["Next"]),
                self.key("7", ["KP_7", "KP_Home"]), self.key("8", ["KP_8", "KP_Up"]), self.key("9", ["KP_9", "KP_Prior"]),
                self.key("+", ["KP_Add"], 1, 2),
            ],
            [
                self.key("Caps", ["Caps_Lock"], 3),
                self.key("A", ["a", "A"]), self.key("S", ["s", "S"]), self.key("D", ["d", "D"]), self.key("F", ["f", "F"]),
                self.key("G", ["g", "G"]), self.key("H", ["h", "H"]), self.key("J", ["j", "J"]), self.key("K", ["k", "K"]),
                self.key("L", ["l", "L"]),
                self.key(";", ["semicolon", "colon"]),
                self.key("'", ["apostrophe", "quotedbl"]),
                self.key("Enter", ["Return"], 3),
                self.key("4", ["KP_4", "KP_Left"]), self.key("5", ["KP_5", "KP_Begin"]), self.key("6", ["KP_6", "KP_Right"]),
            ],
            [
                self.key("Shift", ["Shift_L"], 4),
                self.key("Z", ["z", "Z"]), self.key("X", ["x", "X"]), self.key("C", ["c", "C"]), self.key("V", ["v", "V"]),
                self.key("B", ["b", "B"]), self.key("N", ["n", "N"]), self.key("M", ["m", "M"]),
                self.key(",", ["comma", "less"]),
                self.key(".", ["period", "greater"]),
                self.key("/", ["slash", "question"]),
                self.key("Shift", ["Shift_R"], 4),
                self.key("↑", ["Up"]),
                self.key("1", ["KP_1", "KP_End"]), self.key("2", ["KP_2", "KP_Down"]), self.key("3", ["KP_3", "KP_Next"]),
                self.key("Enter", ["KP_Enter"], 1, 2),
            ],
            [
                self.key("Ctrl", ["Control_L"], 2),
                self.key("Win", ["Super_L", "Meta_L"], 2),
                self.key("Alt", ["Alt_L"], 2),
                self.key("Space", ["space"], 8),
                self.key("Alt", ["Alt_R"], 2),
                self.key("Menu", ["Menu"], 2),
                self.key("Ctrl", ["Control_R"], 2),
                self.key("←", ["Left"]), self.key("↓", ["Down"]), self.key("→", ["Right"]),
                self.key("0", ["KP_0", "KP_Insert"], 2), self.key(".", ["KP_Decimal", "KP_Delete"]),
            ],
        ]

        for r, row in enumerate(rows):
            c = 0
            for key in row:
                btn = tk.Button(
                    keyboard,
                    text=key["label"],
                    width=key["width"] * 2,
                    height=2,
                    bg=KEY_BG,
                    fg=KEY_FG,
                    relief="raised",
                    font=("Segoe UI", 9, "bold"),
                    activebackground=KEY_BG,
                    activeforeground=KEY_FG,
                )
                btn.grid(row=r, column=c, columnspan=key["width"], rowspan=key["rowspan"], padx=2, pady=2, sticky="nsew")
                for key_id in key["ids"]:
                    self._buttons_by_id[key_id] = btn
                c += key["width"]

        controls = tk.Frame(wrapper, bg=WINDOW_BG)
        controls.pack(fill="x", pady=(12, 0))

        self.status_var = tk.StringVar(value="Pressed: 0 keys")
        ttk.Label(controls, textvariable=self.status_var, style="Hint.TLabel").pack(side="left")
        ttk.Button(controls, text="Reset", command=self._reset).pack(side="right")

    @staticmethod
    def key(label: str, ids: list[str], width: int = 1, rowspan: int = 1) -> dict[str, object]:
        return {"label": label, "ids": ids, "width": width, "rowspan": rowspan}

    def _on_key_press(self, event: tk.Event) -> None:
        keysym = event.keysym
        btn = self._buttons_by_id.get(keysym)
        if not btn:
            return
        if keysym not in self._pressed:
            self._pressed.add(keysym)
            btn.configure(bg=PRESSED_BG, fg=PRESSED_FG, activebackground=PRESSED_BG, activeforeground=PRESSED_FG)
            self.status_var.set(f"Pressed: {len(self._pressed)} keys")

    def _reset(self) -> None:
        self._pressed.clear()
        for btn in set(self._buttons_by_id.values()):
            btn.configure(bg=KEY_BG, fg=KEY_FG, activebackground=KEY_BG, activeforeground=KEY_FG)
        self.status_var.set("Pressed: 0 keys")


if __name__ == "__main__":
    app = KeyboardTester()
    app.mainloop()
