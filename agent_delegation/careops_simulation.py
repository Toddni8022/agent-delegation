"""Care operations simulation engine for the Humana AI command center GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import random


WORK_TYPES = (
    "Clinical Triage",
    "Prior Auth",
    "Fraud Review",
    "Care Gap Outreach",
)

SEGMENTS = (
    "Medicare Advantage",
    "Dual Eligible",
    "Commercial",
    "ACA Exchange",
)

SCENARIO_PROFILES = {
    "Flu Season Surge": {
        "arrival_multiplier": 1.8,
        "high_acuity_weight": 1.7,
        "work_weights": [0.42, 0.28, 0.10, 0.20],
    },
    "Value-Based Care Push": {
        "arrival_multiplier": 1.2,
        "high_acuity_weight": 1.1,
        "work_weights": [0.20, 0.26, 0.08, 0.46],
    },
    "Fraud Spike": {
        "arrival_multiplier": 1.3,
        "high_acuity_weight": 1.2,
        "work_weights": [0.14, 0.20, 0.48, 0.18],
    },
}


@dataclass
class CareTask:
    """Represents an operational healthcare task processed by AI agents."""

    task_id: str
    work_type: str
    member_segment: str
    acuity: int
    complexity: int
    expected_cost_impact: float
    wait_minutes: int
    sla_minutes: int
    status: str = "Queued"
    assigned_agent: str = "-"
    remaining_ticks: int = 0
    confidence: float = 0.0
    outcome_note: str = ""

    def urgency_score(self) -> float:
        """Return urgency score used for queue ordering."""
        sla_pressure = min(1.5, self.wait_minutes / max(self.sla_minutes, 1))
        acuity_component = self.acuity * 1.5
        complexity_component = self.complexity * 0.9
        return acuity_component + complexity_component + (sla_pressure * 4.0)

    def risk_contribution(self) -> float:
        """Estimate incremental operational risk this task contributes."""
        breach = 1.0 if self.wait_minutes > self.sla_minutes else 0.0
        return (
            (self.acuity * 1.1)
            + (self.complexity * 0.8)
            + (breach * 4.0)
            + (self.expected_cost_impact / 900.0)
        )


@dataclass
class AgentNode:
    """Agent lane for a specific type of care operations work."""

    name: str
    specialty: str
    capacity: int
    quality: float
    active_tasks: List[CareTask] = field(default_factory=list)
    completed: int = 0
    failed: int = 0

    def utilization(self) -> float:
        """Current lane utilization in [0, 1]."""
        return min(1.0, len(self.active_tasks) / max(self.capacity, 1))


class CareOpsSimulationEngine:
    """Discrete-time simulation engine powering the command center."""

    def __init__(self, seed: int = 7) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self.reset("Flu Season Surge")

    def reset(self, scenario: str = "Flu Season Surge") -> None:
        """Reset simulation state and switch scenario."""
        if scenario not in SCENARIO_PROFILES:
            raise ValueError(f"Unknown scenario '{scenario}'")

        self.scenario = scenario
        self.profile = SCENARIO_PROFILES[scenario]
        self._rng = random.Random(self._seed)
        self.tick = 0
        self._task_counter = 1
        self.queue: List[CareTask] = []
        self.completed_tasks: List[CareTask] = []
        self.event_log: List[str] = [
            f"Scenario initialized: {scenario}",
            "Command center online. AI lanes standing by.",
        ]
        self.backlog_history: List[int] = [0]
        self.total_generated = 0
        self.avoidable_cost_exposed = 0.0
        self.agents: Dict[str, AgentNode] = {
            "Aegis Triage": AgentNode("Aegis Triage", "Clinical Triage", 6, 0.92),
            "Auth Accelerator": AgentNode("Auth Accelerator", "Prior Auth", 5, 0.88),
            "Sentinel Fraud": AgentNode("Sentinel Fraud", "Fraud Review", 4, 0.95),
            "Pulse Outreach": AgentNode("Pulse Outreach", "Care Gap Outreach", 5, 0.90),
        }

    def step(self, intensity: float = 1.0, autonomy_level: float = 0.7) -> None:
        """Advance simulation by one tick."""
        self.tick += 1
        self._age_tasks()
        self._create_arrivals(intensity)
        self._assign_tasks(autonomy_level)
        self._progress_tasks(autonomy_level)
        self._trim_history()
        self.backlog_history.append(len(self.queue))

    def _age_tasks(self) -> None:
        for task in self.queue:
            task.wait_minutes += 4

    def _create_arrivals(self, intensity: float) -> None:
        base_lambda = 3.0 * self.profile["arrival_multiplier"] * intensity
        arrivals = self._rng.randint(1, int(base_lambda + 2))

        for _ in range(arrivals):
            work_type = self._weighted_choice(WORK_TYPES, self.profile["work_weights"])
            acuity = self._sample_acuity()
            complexity = self._rng.randint(1, 5)
            sla_minutes = self._rng.choice((30, 45, 60, 90))
            expected_cost = float(
                self._rng.randint(250, 2400) * (1.0 + (acuity - 3) * 0.2)
            )

            task = CareTask(
                task_id=f"HUM-{self._task_counter:04d}",
                work_type=work_type,
                member_segment=self._rng.choice(SEGMENTS),
                acuity=acuity,
                complexity=complexity,
                expected_cost_impact=max(100.0, round(expected_cost, 2)),
                wait_minutes=0,
                sla_minutes=sla_minutes,
            )
            self._task_counter += 1
            self.total_generated += 1
            self.queue.append(task)

    def _sample_acuity(self) -> int:
        high_weight = self.profile["high_acuity_weight"]
        roll = self._rng.random()
        if roll < 0.10 * high_weight:
            return 5
        if roll < 0.24 * high_weight:
            return 4
        if roll < 0.55:
            return 3
        if roll < 0.82:
            return 2
        return 1

    def _assign_tasks(self, autonomy_level: float) -> None:
        self.queue.sort(key=lambda t: t.urgency_score(), reverse=True)

        for task in list(self.queue):
            candidate_lanes = [
                lane for lane in self.agents.values() if lane.specialty == task.work_type
            ]
            if not candidate_lanes:
                continue
            lane = min(candidate_lanes, key=lambda a: (len(a.active_tasks), -a.quality))
            if len(lane.active_tasks) >= lane.capacity:
                continue

            task.status = "In Progress"
            task.assigned_agent = lane.name
            baseline_ticks = max(1, int(task.complexity + (6 - task.acuity) / 2))
            task.remaining_ticks = max(
                1,
                int(baseline_ticks * (1.25 - min(0.9, autonomy_level))),
            )
            lane.active_tasks.append(task)
            self.queue.remove(task)

    def _progress_tasks(self, autonomy_level: float) -> None:
        for lane in self.agents.values():
            for task in list(lane.active_tasks):
                task.remaining_ticks -= 1
                if task.remaining_ticks > 0:
                    continue

                success_threshold = (
                    lane.quality
                    + (autonomy_level * 0.05)
                    - (task.complexity * 0.03)
                    - (0.02 if task.acuity >= 4 else 0.0)
                )
                task.confidence = max(0.5, min(0.99, success_threshold))
                success = self._rng.random() <= task.confidence

                if success:
                    task.status = "Completed"
                    task.outcome_note = self._completion_note(task)
                    lane.completed += 1
                    self.event_log.append(
                        f"{task.task_id} resolved by {lane.name} ({task.work_type})."
                    )
                else:
                    task.status = "Escalated"
                    task.outcome_note = "Escalated to human specialist"
                    lane.failed += 1
                    self.avoidable_cost_exposed += task.expected_cost_impact * 0.35
                    self.event_log.append(
                        f"{task.task_id} escalated from {lane.name}; human review needed."
                    )

                lane.active_tasks.remove(task)
                self.completed_tasks.append(task)

        self.event_log = self.event_log[-50:]

    def _completion_note(self, task: CareTask) -> str:
        notes = {
            "Clinical Triage": "Care pathway prioritized with predictive acuity map",
            "Prior Auth": "Autopopulated evidence packet approved",
            "Fraud Review": "Anomalous utilization pattern adjudicated",
            "Care Gap Outreach": "Next-best-action outreach sequence generated",
        }
        return notes.get(task.work_type, "Task resolved")

    def _trim_history(self) -> None:
        self.backlog_history = self.backlog_history[-60:]

    def get_snapshot(self) -> Dict[str, object]:
        """Return snapshot consumed by the GUI."""
        in_progress = sum(len(a.active_tasks) for a in self.agents.values())
        completed = len(self.completed_tasks)
        escalated = sum(1 for t in self.completed_tasks if t.status == "Escalated")
        completion_ratio = (
            0.0 if completed == 0 else (completed - escalated) / completed
        )

        recent_window = self.completed_tasks[-20:]
        window_size = max(1, len(recent_window))
        avg_conf = (
            sum(t.confidence for t in recent_window) / window_size if recent_window else 0.0
        )
        throughput_per_hour = round((completed / max(self.tick, 1)) * 15.0, 1)
        risk_index = self._risk_index()

        recommendations = self._recommendations(risk_index, completion_ratio, avg_conf)

        return {
            "tick": self.tick,
            "scenario": self.scenario,
            "queue_size": len(self.queue),
            "in_progress": in_progress,
            "completed": completed,
            "escalated": escalated,
            "throughput_per_hour": throughput_per_hour,
            "auto_resolution_rate": round(completion_ratio * 100.0, 1),
            "avg_confidence": round(avg_conf * 100.0, 1),
            "risk_index": round(risk_index, 1),
            "avoidable_cost_exposed": round(self.avoidable_cost_exposed, 2),
            "recommendations": recommendations,
            "event_log": list(self.event_log[-12:]),
            "backlog_history": list(self.backlog_history),
            "queue": list(sorted(self.queue, key=lambda t: t.urgency_score(), reverse=True)),
            "agents": list(self.agents.values()),
        }

    def _risk_index(self) -> float:
        queued_risk = sum(task.risk_contribution() for task in self.queue)
        active_risk = sum(
            task.risk_contribution()
            for lane in self.agents.values()
            for task in lane.active_tasks
        )
        throughput_guard = max(1.0, len(self.completed_tasks) / max(self.tick, 1))
        return ((queued_risk * 0.7) + (active_risk * 0.3)) / throughput_guard

    def _recommendations(
        self, risk_index: float, completion_ratio: float, avg_confidence: float
    ) -> List[str]:
        recs: List[str] = []

        prior_auth_queue = sum(1 for task in self.queue if task.work_type == "Prior Auth")
        high_acuity_pending = sum(1 for task in self.queue if task.acuity >= 4)
        fraud_pending = sum(1 for task in self.queue if task.work_type == "Fraud Review")

        if risk_index > 60:
            recs.append(
                "Activate surge mode: route low-acuity triage to autonomous self-service."
            )
        if prior_auth_queue >= 7:
            recs.append(
                "Shift 1 lane from outreach to prior-auth to protect approval SLAs."
            )
        if high_acuity_pending >= 6:
            recs.append(
                "Escalate clinical triage model temperature down for safer high-acuity handling."
            )
        if fraud_pending >= 5:
            recs.append(
                "Increase fraud threshold sensitivity and trigger SIU pre-review bundles."
            )
        if completion_ratio < 0.8:
            recs.append(
                "Review autonomy policy: escalation rate is high; add human-in-the-loop checkpoints."
            )
        if avg_confidence < 82:
            recs.append("Retrain weakest lane on last 7-day adjudication feedback set.")

        if not recs:
            recs.append(
                "System stable: maintain policy and reallocate capacity to care gap closure."
            )

        return recs[:4]

    def _weighted_choice(self, values: tuple[str, ...], weights: List[float]) -> str:
        total = sum(weights)
        roll = self._rng.random() * total
        bucket = 0.0
        for value, weight in zip(values, weights):
            bucket += weight
            if roll <= bucket:
                return value
        return values[-1]
