"""Desktop GUI for transcript fact-checking.

Usage:
    python examples/fact_check_gui.py
"""

from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
import sys
from typing import Any

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ModuleNotFoundError:  # pragma: no cover - depends on host OS packages
    tk = None
    filedialog = None
    messagebox = None
    ttk = None

# Ensure local package imports work when launched as `python examples/...`.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_delegation import Task
from agent_delegation.agents import TrumpSpeechFactCheckAgent


def _write_csv_report(result: dict, destination: Path) -> None:
    """Write fact-check results to CSV."""
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["claim", "verdict", "explanation", "source"],
        )
        writer.writeheader()
        for check in result.get("checks", []):
            writer.writerow(
                {
                    "claim": check.get("claim", ""),
                    "verdict": check.get("verdict", ""),
                    "explanation": check.get("explanation", ""),
                    "source": check.get("source", ""),
                }
            )


def _summarize_verdicts(result: dict) -> str:
    """Create a short summary string grouped by verdict."""
    checks = result.get("checks", [])
    if not checks:
        return "No claim-like statements were flagged."

    counts: dict[str, int] = {}
    for item in checks:
        verdict = str(item.get("verdict", "unknown"))
        counts[verdict] = counts.get(verdict, 0) + 1
    parts = [f"{verdict}: {count}" for verdict, count in sorted(counts.items())]
    return ", ".join(parts)


def format_checks_for_display(result: dict) -> str:
    """Render checks in a readable text block for UI and tests."""
    checks = result.get("checks", [])
    checks_count = int(result.get("checks_count", len(checks)))
    if not checks:
        return "No fact-check flags found.\n"

    lines = [f"Checks found: {checks_count}", ""]
    for idx, item in enumerate(checks, start=1):
        lines.append(f"{idx}. [{item.get('verdict', 'unknown')}] {item.get('claim', '')}")
        lines.append(f"   Explanation: {item.get('explanation', '')}")
        lines.append(f"   Source: {item.get('source', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


class FactCheckApp:
    """Simple transcript fact-check GUI app."""

    def __init__(self, root: Any):
        self.root = root
        self.root.title("Trump Transcript Fact Checker")
        self.root.geometry("980x700")

        self.agent = TrumpSpeechFactCheckAgent()
        self.current_result: dict | None = None
        self.current_transcript: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Transcript Fact Checker",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Select a transcript .txt file and click Analyze.",
        )
        subtitle.pack(anchor="w", pady=(0, 10))

        file_row = ttk.Frame(main)
        file_row.pack(fill="x", pady=(0, 8))

        ttk.Label(file_row, text="Transcript file:").pack(side="left")

        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(file_row, textvariable=self.path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=8)

        browse_btn = ttk.Button(file_row, text="Browse...", command=self.browse_file)
        browse_btn.pack(side="left")

        action_row = ttk.Frame(main)
        action_row.pack(fill="x", pady=(0, 8))

        self.analyze_btn = ttk.Button(
            action_row,
            text="Analyze Transcript",
            command=self.analyze_transcript,
        )
        self.analyze_btn.pack(side="left")

        self.save_json_btn = ttk.Button(
            action_row,
            text="Save JSON",
            command=self.save_json_report,
            state="disabled",
        )
        self.save_json_btn.pack(side="left", padx=(8, 0))

        self.save_csv_btn = ttk.Button(
            action_row,
            text="Save CSV",
            command=self.save_csv_report,
            state="disabled",
        )
        self.save_csv_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready.")
        status_label = ttk.Label(main, textvariable=self.status_var)
        status_label.pack(anchor="w", pady=(0, 8))

        self.summary_var = tk.StringVar(value="")
        summary_label = ttk.Label(main, textvariable=self.summary_var)
        summary_label.pack(anchor="w", pady=(0, 8))

        ttk.Label(main, text="Fact-check findings:").pack(anchor="w")

        self.results_text = tk.Text(main, wrap="word", height=28)
        self.results_text.pack(fill="both", expand=True)

    def browse_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select Transcript File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if selected:
            self.path_var.set(selected)

    def analyze_transcript(self) -> None:
        raw_path = self.path_var.get().strip()
        if not raw_path:
            messagebox.showerror("Missing file", "Please choose a transcript file.")
            return

        transcript_path = Path(raw_path)
        if not transcript_path.exists():
            messagebox.showerror("Not found", f"File does not exist:\n{transcript_path}")
            return

        self.analyze_btn.configure(state="disabled")
        self.status_var.set("Analyzing transcript...")
        self.root.update_idletasks()

        try:
            result = asyncio.run(
                self.agent.execute(
                    Task(
                        task_type="trump_fact_check",
                        params={
                            "operation": "fact_check",
                            "transcript_path": str(transcript_path),
                        },
                    )
                )
            )
        except Exception as exc:  # pragma: no cover - GUI error path
            self.status_var.set("Analysis failed.")
            self.analyze_btn.configure(state="normal")
            messagebox.showerror("Error", str(exc))
            return

        self.current_transcript = transcript_path
        self.current_result = result
        self._render_result(result)

        self.save_json_btn.configure(state="normal")
        self.save_csv_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal")
        self.status_var.set(f"Done. Checks found: {result.get('checks_count', 0)}")
        self.summary_var.set(_summarize_verdicts(result))

    def _render_result(self, result: dict) -> None:
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, format_checks_for_display(result))

    def _default_output_path(self, suffix: str) -> Path:
        if self.current_transcript:
            return self.current_transcript.with_name(
                f"{self.current_transcript.stem}_fact_check_report.{suffix}"
            )
        return Path(f"fact_check_report.{suffix}")

    def save_json_report(self) -> None:
        if not self.current_result:
            return
        default_path = self._default_output_path("json")
        target = filedialog.asksaveasfilename(
            title="Save JSON Report",
            defaultextension=".json",
            initialfile=default_path.name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not target:
            return
        output_path = Path(target)
        output_path.write_text(json.dumps(self.current_result, indent=2), encoding="utf-8")
        messagebox.showinfo("Saved", f"JSON report saved:\n{output_path}")

    def save_csv_report(self) -> None:
        if not self.current_result:
            return
        default_path = self._default_output_path("csv")
        target = filedialog.asksaveasfilename(
            title="Save CSV Report",
            defaultextension=".csv",
            initialfile=default_path.name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not target:
            return
        output_path = Path(target)
        _write_csv_report(self.current_result, output_path)
        messagebox.showinfo("Saved", f"CSV report saved:\n{output_path}")


def main() -> None:
    if tk is None:
        raise RuntimeError(
            "tkinter is not available in this Python build. "
            "Install python3-tk (Linux) or use standard Python on Windows/macOS."
        )

    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        # Theme availability differs across platforms; default theme is fine.
        pass
    app = FactCheckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
