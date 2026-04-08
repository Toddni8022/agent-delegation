"""Tests for fiber run estimator tool."""

import json

import pytest

from agent_delegation.tools.fiber_run_estimator import (
    CabinetLocation,
    calculate_fiber_run,
    load_cabinet_locations_from_dctrack_api,
    load_cabinet_locations,
)


def test_calculate_fiber_run_manhattan_breakdown():
    """Should include horizontal, vertical, turns, loops, and slack."""
    cabinets = {
        "A-14": CabinetLocation(
            cabinet_id="A-14", x_ft=10, y_ft=20, elevation_ft=0, entry_height_ft=2
        ),
        "B-22": CabinetLocation(
            cabinet_id="B-22", x_ft=160, y_ft=170, elevation_ft=0, entry_height_ft=2
        ),
    }

    estimate = calculate_fiber_run(
        cabinets,
        "A-14",
        "B-22",
        route_height_ft=10,
        routing_mode="manhattan",
        turns=3,
        turn_allowance_ft=2.0,
        service_loop_ft_per_end=5.0,
        slack_percent=10.0,
        round_up_ft=5.0,
    )

    assert estimate.horizontal_ft == pytest.approx(300.0)
    assert estimate.vertical_ft == pytest.approx(16.0)
    assert estimate.turn_allowance_ft == pytest.approx(6.0)
    assert estimate.service_loop_ft == pytest.approx(10.0)
    assert estimate.subtotal_ft == pytest.approx(332.0)
    assert estimate.slack_ft == pytest.approx(33.2)
    assert estimate.total_ft == pytest.approx(365.2)
    assert estimate.recommended_cut_ft == pytest.approx(370.0)


def test_calculate_fiber_run_euclidean_mode():
    """Should support straight-line horizontal estimate for comparison."""
    cabinets = {
        "A": CabinetLocation(cabinet_id="A", x_ft=0, y_ft=0, elevation_ft=0, entry_height_ft=2),
        "B": CabinetLocation(cabinet_id="B", x_ft=300, y_ft=400, elevation_ft=0, entry_height_ft=2),
    }

    estimate = calculate_fiber_run(
        cabinets,
        "A",
        "B",
        route_height_ft=10,
        routing_mode="euclidean",
        slack_percent=0,
        round_up_ft=0,
    )

    assert estimate.horizontal_ft == pytest.approx(500.0)
    assert estimate.vertical_ft == pytest.approx(16.0)
    assert estimate.total_ft == pytest.approx(526.0)
    assert estimate.recommended_cut_ft == pytest.approx(526.0)


def test_calculate_fiber_run_rejects_unknown_cabinet():
    """Should fail fast when cabinet IDs do not exist."""
    normalized: dict[str, CabinetLocation] = {}
    with pytest.raises(KeyError):
        calculate_fiber_run(normalized, "A", "B")


def test_load_cabinet_locations_from_csv(tmp_path):
    """Should parse required and optional CSV columns."""
    csv_file = tmp_path / "cabinets.csv"
    csv_file.write_text(
        "\n".join(
            [
                "cabinet_id,x_ft,y_ft,elevation_ft,entry_height_ft",
                "A-14,10,20,0,2",
                "B-22,160,170,0,2",
            ]
        ),
        encoding="utf-8",
    )

    cabinets = load_cabinet_locations(csv_file)
    assert set(cabinets.keys()) == {"A-14", "B-22"}
    assert cabinets["A-14"].x_ft == pytest.approx(10.0)
    assert cabinets["B-22"].entry_elevation_ft == pytest.approx(2.0)


def test_load_cabinet_locations_from_json_object(tmp_path):
    """Should parse JSON mapping keyed by cabinet ID."""
    json_file = tmp_path / "cabinets.json"
    json_file.write_text(
        json.dumps(
            {
                "A-14": {"x_ft": 10, "y_ft": 20, "entry_height_ft": 2},
                "B-22": {"x_ft": 160, "y_ft": 170, "entry_height_ft": 2},
            }
        ),
        encoding="utf-8",
    )

    cabinets = load_cabinet_locations(json_file)
    assert cabinets["A-14"].cabinet_id == "A-14"
    assert cabinets["B-22"].y_ft == pytest.approx(170.0)


def test_load_cabinet_locations_rejects_bad_extension(tmp_path):
    """Should require CSV or JSON file input."""
    input_file = tmp_path / "cabinets.txt"
    input_file.write_text("irrelevant", encoding="utf-8")

    with pytest.raises(ValueError, match="must be .csv or .json"):
        load_cabinet_locations(input_file)


def test_load_cabinet_locations_from_dctrack_api(monkeypatch):
    """Should parse dcTrack-style API JSON and map field names."""
    payload = {
        "data": {
            "items": [
                {"name": "A-14", "x": 10, "y": 20, "z": 0, "entry": 2},
                {"name": "B-22", "x": 160, "y": 170, "z": 0, "entry": 2},
            ]
        }
    }

    class _DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    def _fake_urlopen(_req, timeout):
        assert timeout == pytest.approx(15.0)
        return _DummyResponse()

    monkeypatch.setattr(
        "agent_delegation.tools.fiber_run_estimator.urllib_request.urlopen",
        _fake_urlopen,
    )

    cabinets = load_cabinet_locations_from_dctrack_api(
        "https://dctrack.local/api/cabinets",
        token="secret",
        timeout_sec=15.0,
        data_path="data.items",
        field_cabinet_id="name",
        field_x="x",
        field_y="y",
        field_elevation="z",
        field_entry_height="entry",
    )

    assert cabinets["A-14"].x_ft == pytest.approx(10.0)
    assert cabinets["B-22"].y_ft == pytest.approx(170.0)
