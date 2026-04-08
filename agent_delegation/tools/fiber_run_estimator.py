"""Fiber run estimation helper for data center cabinet routes."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CabinetLocation:
    """Physical cabinet coordinates and entry point details in feet."""

    cabinet_id: str
    x_ft: float
    y_ft: float
    elevation_ft: float = 0.0
    entry_height_ft: float = 0.0

    @property
    def entry_elevation_ft(self) -> float:
        """Absolute elevation of the cable entry point."""
        return self.elevation_ft + self.entry_height_ft


@dataclass(frozen=True)
class FiberRunEstimate:
    """Detailed fiber run estimate breakdown."""

    from_cabinet: str
    to_cabinet: str
    routing_mode: str
    horizontal_ft: float
    vertical_ft: float
    turn_allowance_ft: float
    service_loop_ft: float
    subtotal_ft: float
    slack_ft: float
    total_ft: float
    recommended_cut_ft: float


def _as_float(value: Any, field_name: str) -> float:
    """Convert value to float with a readable error."""
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for '{field_name}': {value!r}") from exc


def _cabinet_from_mapping(cabinet_id: str, raw: dict[str, Any]) -> CabinetLocation:
    """Build a CabinetLocation from a dict-like object."""
    return CabinetLocation(
        cabinet_id=cabinet_id,
        x_ft=_as_float(raw.get("x_ft"), "x_ft"),
        y_ft=_as_float(raw.get("y_ft"), "y_ft"),
        elevation_ft=_as_float(raw.get("elevation_ft", 0.0), "elevation_ft"),
        entry_height_ft=_as_float(raw.get("entry_height_ft", 0.0), "entry_height_ft"),
    )


def _load_csv(path: Path) -> dict[str, CabinetLocation]:
    """Load cabinet locations from a CSV file."""
    cabinets: dict[str, CabinetLocation] = {}
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_headers = {"cabinet_id", "x_ft", "y_ft"}
        missing_headers = required_headers - set(reader.fieldnames or [])
        if missing_headers:
            missing = ", ".join(sorted(missing_headers))
            raise ValueError(f"CSV is missing required headers: {missing}")

        for row in reader:
            cabinet_id = (row.get("cabinet_id") or "").strip()
            if not cabinet_id:
                raise ValueError("Every CSV row must include a cabinet_id value.")
            if cabinet_id in cabinets:
                raise ValueError(f"Duplicate cabinet_id found: {cabinet_id}")
            cabinets[cabinet_id] = _cabinet_from_mapping(cabinet_id, row)

    if not cabinets:
        raise ValueError("Cabinet file is empty.")
    return cabinets


def _load_json(path: Path) -> dict[str, CabinetLocation]:
    """Load cabinet locations from a JSON file."""
    with path.open(encoding="utf-8") as json_file:
        payload = json.load(json_file)

    cabinets: dict[str, CabinetLocation] = {}
    if isinstance(payload, dict):
        for cabinet_id, raw in payload.items():
            if not isinstance(raw, dict):
                raise ValueError("Each JSON object value must be an object.")
            if cabinet_id in cabinets:
                raise ValueError(f"Duplicate cabinet_id found: {cabinet_id}")
            cabinets[cabinet_id] = _cabinet_from_mapping(cabinet_id, raw)
    elif isinstance(payload, list):
        for raw in payload:
            if not isinstance(raw, dict):
                raise ValueError("Each JSON list item must be an object.")
            cabinet_id = str(raw.get("cabinet_id", "")).strip()
            if not cabinet_id:
                raise ValueError("Each JSON item must include 'cabinet_id'.")
            if cabinet_id in cabinets:
                raise ValueError(f"Duplicate cabinet_id found: {cabinet_id}")
            cabinets[cabinet_id] = _cabinet_from_mapping(cabinet_id, raw)
    else:
        raise ValueError("JSON cabinet file must be an object or list.")

    if not cabinets:
        raise ValueError("Cabinet file is empty.")
    return cabinets


def load_cabinet_locations(path: str | Path) -> dict[str, CabinetLocation]:
    """Load cabinet locations from JSON or CSV."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Cabinet file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _load_csv(file_path)
    if suffix == ".json":
        return _load_json(file_path)
    raise ValueError("Cabinet file must be .csv or .json")


def calculate_fiber_run(
    cabinets: dict[str, CabinetLocation],
    from_cabinet: str,
    to_cabinet: str,
    *,
    route_height_ft: float = 10.0,
    routing_mode: str = "manhattan",
    turns: int = 0,
    turn_allowance_ft: float = 2.0,
    service_loop_ft_per_end: float = 5.0,
    slack_percent: float = 10.0,
    round_up_ft: float = 5.0,
) -> FiberRunEstimate:
    """Calculate a practical fiber run estimate between cabinet locations."""
    if from_cabinet not in cabinets:
        raise KeyError(f"Unknown source cabinet: {from_cabinet}")
    if to_cabinet not in cabinets:
        raise KeyError(f"Unknown destination cabinet: {to_cabinet}")
    if turns < 0:
        raise ValueError("turns must be >= 0")
    if route_height_ft < 0:
        raise ValueError("route_height_ft must be >= 0")
    if turn_allowance_ft < 0:
        raise ValueError("turn_allowance_ft must be >= 0")
    if service_loop_ft_per_end < 0:
        raise ValueError("service_loop_ft_per_end must be >= 0")
    if slack_percent < 0:
        raise ValueError("slack_percent must be >= 0")
    if round_up_ft < 0:
        raise ValueError("round_up_ft must be >= 0")

    source = cabinets[from_cabinet]
    destination = cabinets[to_cabinet]
    dx = abs(destination.x_ft - source.x_ft)
    dy = abs(destination.y_ft - source.y_ft)

    if routing_mode == "manhattan":
        horizontal_ft = dx + dy
    elif routing_mode == "euclidean":
        horizontal_ft = math.hypot(dx, dy)
    else:
        raise ValueError("routing_mode must be 'manhattan' or 'euclidean'")

    vertical_ft = abs(route_height_ft - source.entry_elevation_ft) + abs(
        route_height_ft - destination.entry_elevation_ft
    )
    turn_total_ft = turns * turn_allowance_ft
    service_loop_ft = service_loop_ft_per_end * 2
    subtotal_ft = horizontal_ft + vertical_ft + turn_total_ft + service_loop_ft
    slack_ft = subtotal_ft * (slack_percent / 100.0)
    total_ft = subtotal_ft + slack_ft

    if round_up_ft > 0:
        recommended_cut_ft = math.ceil(total_ft / round_up_ft) * round_up_ft
    else:
        recommended_cut_ft = total_ft

    return FiberRunEstimate(
        from_cabinet=from_cabinet,
        to_cabinet=to_cabinet,
        routing_mode=routing_mode,
        horizontal_ft=horizontal_ft,
        vertical_ft=vertical_ft,
        turn_allowance_ft=turn_total_ft,
        service_loop_ft=service_loop_ft,
        subtotal_ft=subtotal_ft,
        slack_ft=slack_ft,
        total_ft=total_ft,
        recommended_cut_ft=recommended_cut_ft,
    )


def _format_estimate(estimate: FiberRunEstimate, turns: int, per_turn_ft: float) -> str:
    """Create a readable report from a fiber run estimate."""
    lines = [
        f"Fiber run estimate: {estimate.from_cabinet} -> {estimate.to_cabinet}",
        f"Routing mode: {estimate.routing_mode}",
        f"Horizontal distance: {estimate.horizontal_ft:.2f} ft",
        f"Vertical drops/rises: {estimate.vertical_ft:.2f} ft",
        f"Turn allowance ({turns} turns @ {per_turn_ft:.2f} ft): {estimate.turn_allowance_ft:.2f} ft",
        f"Service loops (both ends): {estimate.service_loop_ft:.2f} ft",
        f"Subtotal before slack: {estimate.subtotal_ft:.2f} ft",
        f"Slack allowance: {estimate.slack_ft:.2f} ft",
        f"Estimated total run: {estimate.total_ft:.2f} ft",
        f"Recommended cut length: {estimate.recommended_cut_ft:.2f} ft",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Estimate fiber run length between two data center cabinets."
    )
    parser.add_argument("--cabinet-file", required=True, help="Path to .csv or .json cabinet file.")
    parser.add_argument("--from-cabinet", required=True, help="Source cabinet identifier.")
    parser.add_argument("--to-cabinet", required=True, help="Destination cabinet identifier.")
    parser.add_argument("--route-height-ft", type=float, default=10.0, help="Overhead route height in feet.")
    parser.add_argument(
        "--routing-mode",
        choices=("manhattan", "euclidean"),
        default="manhattan",
        help="Route mode: 'manhattan' follows tray/grid paths, 'euclidean' is straight-line.",
    )
    parser.add_argument("--turns", type=int, default=0, help="Expected number of turns.")
    parser.add_argument("--turn-allowance-ft", type=float, default=2.0, help="Extra feet per turn.")
    parser.add_argument(
        "--service-loop-ft-per-end",
        type=float,
        default=5.0,
        help="Service loop reserve per end in feet.",
    )
    parser.add_argument("--slack-percent", type=float, default=10.0, help="Extra slack percent.")
    parser.add_argument(
        "--round-up-ft",
        type=float,
        default=5.0,
        help="Round up recommendation to this increment (0 disables rounding).",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        cabinets = load_cabinet_locations(args.cabinet_file)
        estimate = calculate_fiber_run(
            cabinets,
            args.from_cabinet,
            args.to_cabinet,
            route_height_ft=args.route_height_ft,
            routing_mode=args.routing_mode,
            turns=args.turns,
            turn_allowance_ft=args.turn_allowance_ft,
            service_loop_ft_per_end=args.service_loop_ft_per_end,
            slack_percent=args.slack_percent,
            round_up_ft=args.round_up_ft,
        )
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    print(_format_estimate(estimate, args.turns, args.turn_allowance_ft))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
