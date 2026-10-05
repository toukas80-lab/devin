"""DEVIN-PDF.exe entry point: run the drop-folder batch and show the report in a window.

DEVIN-PDF.exe [base-dir]        (base-dir defaults to C:\\Soft1)
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from softone_pilot.dropfolder import DEFAULT_BASE, REPORT_FILE, run


def show_report(title: str, lines: list[str]) -> None:
    root = tk.Tk()
    root.title(title)
    root.geometry("1100x600")
    text = tk.Text(root, wrap=tk.NONE, font=("Consolas", 10))
    text.insert("1.0", "\n".join(lines))
    text.configure(state=tk.DISABLED)
    scroll_y = ttk.Scrollbar(root, orient=tk.VERTICAL, command=text.yview)
    scroll_x = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=text.xview)
    text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    ttk.Button(root, text="Κλείσιμο", command=root.destroy).pack(side=tk.BOTTOM, pady=6)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    text.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


def main() -> None:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BASE
    try:
        lines = run(base)
        title = "DEVIN PDF -> SoftOne"
    except Exception as exc:  # shown to the user instead of a silent crash
        lines = [f"ΣΦΑΛΜΑ: {exc}"]
        title = "DEVIN PDF -> SoftOne: ΣΦΑΛΜΑ"
    try:
        (base / REPORT_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass
    show_report(title, lines)


if __name__ == "__main__":
    main()
