from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from softone_pilot.audit import write_dry_run_audit
from softone_pilot.config import default_config, load_config
from softone_pilot.planner import prepare_batch


class PilotWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SoftOne PDF Pilot")
        self.geometry("1050x600")
        self.pdfs: list[Path] = []
        self.config_path: Path | None = None
        self._build()

    def _build(self) -> None:
        toolbar = ttk.Frame(self, padding=10)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Επιλογή PDF", command=self._select_pdfs).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Ρυθμίσεις", command=self._select_config).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(toolbar, text="Dry-run", command=self._dry_run).pack(side=tk.LEFT)
        self.status = ttk.Label(toolbar, text="Καμία πραγματική καταχώριση")
        self.status.pack(side=tk.RIGHT)

        columns = ("file", "issuer", "number", "date", "net", "vat", "total", "status")
        self.table = ttk.Treeview(self, columns=columns, show="headings")
        headings = {
            "file": "Αρχείο",
            "issuer": "Εκδότης",
            "number": "Αριθμός",
            "date": "Ημερομηνία",
            "net": "Καθαρή",
            "vat": "ΦΠΑ",
            "total": "Σύνολο",
            "status": "Κατάσταση",
        }
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=125, anchor=tk.W)
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.details = tk.Text(self, height=10, wrap=tk.WORD)
        self.details.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _select_pdfs(self) -> None:
        paths = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        self.pdfs = [Path(path) for path in paths]
        self.status.config(text=f"{len(self.pdfs)} PDF επιλέχθηκαν")

    def _select_config(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.config_path = Path(path)
            self.status.config(text=f"Ρυθμίσεις: {self.config_path.name}")

    def _dry_run(self) -> None:
        if not self.pdfs:
            messagebox.showwarning("SoftOne PDF Pilot", "Επίλεξε πρώτα PDF")
            return
        try:
            config = load_config(self.config_path) if self.config_path else default_config()
            prepared, errors = prepare_batch(
                self.pdfs,
                config,
                use_sql=bool(self.config_path and config.sql.enabled),
            )
            write_dry_run_audit("pilot-data/audit.jsonl", prepared, errors)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("SoftOne PDF Pilot", str(exc))
            return

        for row in self.table.get_children():
            self.table.delete(row)
        detail_lines = []
        for item in prepared:
            invoice = item.invoice
            self.table.insert(
                "",
                tk.END,
                values=(
                    invoice.source_path.name,
                    invoice.supplier_name,
                    invoice.document_number,
                    invoice.document_date.strftime("%d/%m/%Y"),
                    f"{invoice.net_value:.2f}",
                    f"{invoice.vat_value:.2f}",
                    f"{invoice.total_value:.2f}",
                    "Έτοιμο" if item.ready else "Μπλοκαρισμένο",
                ),
            )
            detail_lines.extend(
                [
                    f"{invoice.source_path.name}: {message}"
                    for message in (*item.errors, *item.warnings)
                ]
            )
        detail_lines.extend(errors)
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", "\n".join(detail_lines) or "Dry-run ολοκληρώθηκε χωρίς σφάλματα")
        self.status.config(text="Dry-run ολοκληρώθηκε — δεν έγινε καταχώριση")


def main() -> None:
    PilotWindow().mainloop()


if __name__ == "__main__":
    main()
