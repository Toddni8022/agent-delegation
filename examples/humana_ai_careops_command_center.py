"""Humana AI CareOps Command Center.

Run:
    python examples/humana_ai_careops_command_center.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from agent_delegation.careops_simulation import (
    CareOpsSimulationEngine,
    SCENARIO_PROFILES,
)


BG = "#0b1221"
PANEL = "#111c33"
CARD = "#1a2847"
TEXT = "#d8e5ff"
MUTED = "#9cb2d9"
ACCENT = "#6dd3ff"
GOOD = "#40c463"
WARN = "#ffb84d"
RISK = "#ff6b6b"


class CommandCenterApp:
    """Desktop GUI for healthcare AI operations simulation."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Humana AI CareOps Command Center")
        self.root.geometry("1380x860")
        self.root.configure(bg=BG)

        self.engine = CareOpsSimulationEngine(seed=11)
        self.running = False

        self.scenario_var = tk.StringVar(value="Flu Season Surge")
        self.intensity_var = tk.DoubleVar(value=1.0)
        self.autonomy_var = tk.DoubleVar(value=0.76)
        self.speed_var = tk.IntVar(value=700)

        self._build_styles()
        self._build_ui()
        self._refresh_ui()
        self.root.after(200, self._loop)

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Card.TFrame", background=CARD)
        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG,
            foreground=MUTED,
            font=("Segoe UI", 11),
        )
        style.configure(
            "CardHeader.TLabel",
            background=CARD,
            foreground=MUTED,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "CardValue.TLabel",
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Control.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.configure("Control.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure(
            "Treeview",
            background="#0f1730",
            foreground=TEXT,
            fieldbackground="#0f1730",
            rowheight=24,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#203154",
            foreground=TEXT,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#264b80")],
            foreground=[("selected", TEXT)],
        )
        style.configure("TCombobox", fieldbackground="#0f1730", foreground=TEXT)

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root, style="TFrame")
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        header = ttk.Frame(shell, style="TFrame")
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="Humana AI CareOps Command Center", style="Title.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="Real-time autonomous operations simulation for utilization, triage, prior-auth, and fraud lanes.",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        self._build_controls(shell)
        self._build_kpis(shell)
        self._build_panels(shell)

    def _build_controls(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Scenario", style="Control.TLabel").grid(row=0, column=0, sticky="w")
        self.scenario_box = ttk.Combobox(
            controls,
            textvariable=self.scenario_var,
            values=list(SCENARIO_PROFILES.keys()),
            state="readonly",
            width=22,
        )
        self.scenario_box.grid(row=1, column=0, padx=(0, 14), sticky="w")

        ttk.Label(controls, text="Case Arrival Intensity", style="Control.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Scale(
            controls,
            from_=0.5,
            to=1.8,
            variable=self.intensity_var,
            orient=tk.HORIZONTAL,
            length=220,
        ).grid(row=1, column=1, padx=(0, 14))

        ttk.Label(controls, text="Autonomy Confidence", style="Control.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        ttk.Scale(
            controls,
            from_=0.45,
            to=0.95,
            variable=self.autonomy_var,
            orient=tk.HORIZONTAL,
            length=220,
        ).grid(row=1, column=2, padx=(0, 14))

        ttk.Label(controls, text="Simulation Speed (ms/tick)", style="Control.TLabel").grid(
            row=0, column=3, sticky="w"
        )
        ttk.Scale(
            controls,
            from_=250,
            to=1200,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=220,
        ).grid(row=1, column=3, padx=(0, 14))

        btns = ttk.Frame(controls, style="Panel.TFrame")
        btns.grid(row=1, column=4, sticky="e")
        ttk.Button(btns, text="Start", style="Control.TButton", command=self._start).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Pause", style="Control.TButton", command=self._pause).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Step", style="Control.TButton", command=self._step_once).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Reset", style="Control.TButton", command=self._reset).pack(
            side=tk.LEFT, padx=4
        )

    def _build_kpis(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent, style="TFrame")
        row.pack(fill=tk.X, pady=(0, 10))

        self.kpi_labels: dict[str, ttk.Label] = {}
        for idx, title in enumerate(
            (
                "Active Queue",
                "SLA Risk Index",
                "Throughput / Hour",
                "Auto-Resolution Rate",
                "Avoidable Cost Exposed",
            )
        ):
            card = ttk.Frame(row, style="Card.TFrame", padding=(14, 10))
            card.grid(row=0, column=idx, padx=(0 if idx == 0 else 8, 0), sticky="nsew")
            row.columnconfigure(idx, weight=1)
            ttk.Label(card, text=title, style="CardHeader.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="--", style="CardValue.TLabel")
            value.pack(anchor="w", pady=(6, 2))
            self.kpi_labels[title] = value

    def _build_panels(self, parent: ttk.Frame) -> None:
        body = ttk.Frame(parent, style="TFrame")
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=3)
        body.rowconfigure(1, weight=2)

        queue_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        queue_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        ttk.Label(queue_panel, text="Operational Queue", style="Control.TLabel").pack(anchor="w")
        self.queue_tree = ttk.Treeview(
            queue_panel,
            columns=("task", "type", "acuity", "wait", "sla", "segment", "risk"),
            show="headings",
            height=13,
        )
        for col, width in (
            ("task", 90),
            ("type", 155),
            ("acuity", 60),
            ("wait", 75),
            ("sla", 75),
            ("segment", 150),
            ("risk", 90),
        ):
            self.queue_tree.heading(col, text=col.upper())
            self.queue_tree.column(col, width=width, stretch=False)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        chart_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        chart_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(chart_panel, text="Backlog Trend (last 60 ticks)", style="Control.TLabel").pack(
            anchor="w"
        )
        self.backlog_canvas = tk.Canvas(
            chart_panel,
            height=180,
            bg="#0f1730",
            highlightthickness=0,
        )
        self.backlog_canvas.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        right_top = ttk.Frame(body, style="Panel.TFrame", padding=10)
        right_top.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        right_top.rowconfigure(0, weight=1)
        right_top.rowconfigure(1, weight=1)

        lanes = ttk.Frame(right_top, style="Panel.TFrame")
        lanes.grid(row=0, column=0, sticky="nsew")
        ttk.Label(lanes, text="AI Lanes", style="Control.TLabel").pack(anchor="w")
        self.agent_tree = ttk.Treeview(
            lanes,
            columns=("lane", "specialty", "util", "completed", "failed"),
            show="headings",
            height=6,
        )
        for col, width in (
            ("lane", 130),
            ("specialty", 140),
            ("util", 70),
            ("completed", 85),
            ("failed", 70),
        ):
            self.agent_tree.heading(col, text=col.upper())
            self.agent_tree.column(col, width=width, stretch=False)
        self.agent_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        recs = ttk.Frame(right_top, style="Panel.TFrame")
        recs.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        ttk.Label(
            recs,
            text="AI Recommendations",
            style="Control.TLabel",
        ).pack(anchor="w")
        self.recommendations = tk.Listbox(
            recs,
            bg="#0f1730",
            fg=TEXT,
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#264b80",
            font=("Segoe UI", 10),
        )
        self.recommendations.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        event_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        event_panel.grid(row=1, column=1, sticky="nsew")
        ttk.Label(event_panel, text="Command Timeline", style="Control.TLabel").pack(anchor="w")
        self.event_text = tk.Text(
            event_panel,
            bg="#0f1730",
            fg=TEXT,
            borderwidth=0,
            highlightthickness=0,
            font=("Consolas", 10),
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.event_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def _start(self) -> None:
        if self.engine.scenario != self.scenario_var.get():
            self.engine.reset(self.scenario_var.get())
        self.running = True

    def _pause(self) -> None:
        self.running = False

    def _step_once(self) -> None:
        self.engine.step(
            intensity=float(self.intensity_var.get()),
            autonomy_level=float(self.autonomy_var.get()),
        )
        self._refresh_ui()

    def _reset(self) -> None:
        self.running = False
        self.engine.reset(self.scenario_var.get())
        self._refresh_ui()

    def _loop(self) -> None:
        if self.running:
            self.engine.step(
                intensity=float(self.intensity_var.get()),
                autonomy_level=float(self.autonomy_var.get()),
            )
            self._refresh_ui()
        self.root.after(int(self.speed_var.get()), self._loop)

    def _refresh_ui(self) -> None:
        snap = self.engine.get_snapshot()

        self._set_card("Active Queue", f"{snap['queue_size']}  |  {snap['in_progress']} active")
        risk_value = float(snap["risk_index"])
        self._set_card("SLA Risk Index", f"{risk_value:.1f}")
        self._set_card("Throughput / Hour", f"{snap['throughput_per_hour']}")
        self._set_card("Auto-Resolution Rate", f"{snap['auto_resolution_rate']}%")
        self._set_card(
            "Avoidable Cost Exposed",
            f"${snap['avoidable_cost_exposed']:,.0f}",
        )

        risk_label = self.kpi_labels["SLA Risk Index"]
        if risk_value > 65:
            risk_label.configure(foreground=RISK)
        elif risk_value > 40:
            risk_label.configure(foreground=WARN)
        else:
            risk_label.configure(foreground=GOOD)

        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        for task in list(snap["queue"])[:20]:
            self.queue_tree.insert(
                "",
                tk.END,
                values=(
                    task.task_id,
                    task.work_type,
                    task.acuity,
                    f"{task.wait_minutes}m",
                    f"{task.sla_minutes}m",
                    task.member_segment,
                    f"{task.risk_contribution():.1f}",
                ),
            )

        for item in self.agent_tree.get_children():
            self.agent_tree.delete(item)
        for lane in snap["agents"]:
            self.agent_tree.insert(
                "",
                tk.END,
                values=(
                    lane.name,
                    lane.specialty,
                    f"{lane.utilization() * 100:.0f}%",
                    lane.completed,
                    lane.failed,
                ),
            )

        self.recommendations.delete(0, tk.END)
        for recommendation in snap["recommendations"]:
            self.recommendations.insert(tk.END, f"• {recommendation}")

        self.event_text.configure(state=tk.NORMAL)
        self.event_text.delete("1.0", tk.END)
        self.event_text.insert(
            tk.END,
            f"Tick: {snap['tick']} | Scenario: {snap['scenario']} | Avg confidence: {snap['avg_confidence']}%\n\n",
        )
        for line in snap["event_log"]:
            self.event_text.insert(tk.END, f"• {line}\n")
        self.event_text.configure(state=tk.DISABLED)

        self._draw_backlog(snap["backlog_history"])

    def _set_card(self, key: str, value: str) -> None:
        label = self.kpi_labels[key]
        if key != "SLA Risk Index":
            label.configure(foreground=TEXT)
        label.configure(text=value)

    def _draw_backlog(self, history: list[int]) -> None:
        canvas = self.backlog_canvas
        canvas.delete("all")
        w = max(canvas.winfo_width(), 100)
        h = max(canvas.winfo_height(), 60)
        pad = 18
        canvas.create_rectangle(0, 0, w, h, fill="#0f1730", outline="#0f1730")
        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#2b3b63")
        canvas.create_line(pad, pad, pad, h - pad, fill="#2b3b63")

        if len(history) < 2:
            return

        max_val = max(1, max(history))
        x_step = (w - (pad * 2)) / max(1, len(history) - 1)
        points = []
        for i, val in enumerate(history):
            x = pad + (i * x_step)
            y = h - pad - ((val / max_val) * (h - (pad * 2)))
            points.extend((x, y))
        canvas.create_line(*points, fill=ACCENT, width=2, smooth=True)
        canvas.create_text(
            w - 64,
            pad + 8,
            text=f"max: {max_val}",
            fill=MUTED,
            font=("Segoe UI", 9),
        )


def main() -> None:
    root = tk.Tk()
    app = CommandCenterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
