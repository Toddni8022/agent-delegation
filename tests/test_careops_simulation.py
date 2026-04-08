"""Tests for care operations simulation engine."""

from agent_delegation.careops_simulation import (
    CareOpsSimulationEngine,
    CareTask,
)


def test_reset_with_unknown_scenario_raises() -> None:
    """Unknown scenarios should fail fast."""
    engine = CareOpsSimulationEngine(seed=3)
    try:
        engine.reset("Unknown Scenario")
    except ValueError as exc:
        assert "Unknown scenario" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown scenario")


def test_step_progresses_simulation_and_generates_metrics() -> None:
    """Stepping should create work and produce meaningful metrics."""
    engine = CareOpsSimulationEngine(seed=7)
    for _ in range(14):
        engine.step(intensity=1.1, autonomy_level=0.82)

    snapshot = engine.get_snapshot()
    assert snapshot["tick"] == 14
    assert engine.total_generated > 0
    assert snapshot["completed"] > 0
    assert snapshot["throughput_per_hour"] > 0
    assert len(snapshot["recommendations"]) >= 1


def test_assigned_tasks_match_lane_specialty() -> None:
    """Assignment should only route tasks to matching specialty lanes."""
    engine = CareOpsSimulationEngine(seed=9)
    for _ in range(8):
        engine.step(intensity=1.25, autonomy_level=0.75)

    specialty_by_lane = {
        lane.name: lane.specialty
        for lane in engine.agents.values()
    }

    for lane in engine.agents.values():
        for task in lane.active_tasks:
            assert task.work_type == lane.specialty

    for task in engine.completed_tasks:
        if task.assigned_agent != "-":
            assert task.work_type == specialty_by_lane[task.assigned_agent]


def test_risk_index_increases_for_high_acuity_sla_breach_queue() -> None:
    """Risk index should increase for overdue high-acuity queues."""
    engine = CareOpsSimulationEngine(seed=5)
    engine.reset("Value-Based Care Push")
    low_risk_snapshot = engine.get_snapshot()

    engine.queue = [
        CareTask(
            task_id="HUM-T1",
            work_type="Clinical Triage",
            member_segment="Medicare Advantage",
            acuity=5,
            complexity=5,
            expected_cost_impact=2400.0,
            wait_minutes=95,
            sla_minutes=30,
        ),
        CareTask(
            task_id="HUM-T2",
            work_type="Prior Auth",
            member_segment="Dual Eligible",
            acuity=4,
            complexity=5,
            expected_cost_impact=1850.0,
            wait_minutes=88,
            sla_minutes=30,
        ),
    ]
    high_risk_snapshot = engine.get_snapshot()

    assert high_risk_snapshot["risk_index"] > low_risk_snapshot["risk_index"]
