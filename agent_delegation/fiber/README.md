# Fiber Run Estimator (dcTrack + Cabinet Files)

Estimate realistic fiber run length between two data center cabinets, including:

- Horizontal routing distance
- Vertical drops/rises
- Turn allowance
- Service loops
- Slack percentage
- Rounded cut recommendation

You can run it with either:

1. A local cabinet coordinate file (`.csv` / `.json`)
2. A dcTrack API endpoint (JSON payload)

---

## File Location

Main script:

- `agent_delegation/fiber/fiber_run_estimator.py`

Sample cabinet file:

- `agent_delegation/fiber/cabinet_locations_sample.csv`

---

## Install

From repo root:

```bash
python3 -m pip install -e .
```

---

## Usage: Cabinet File Mode

```bash
fiber-run-estimator \
  --cabinet-file agent_delegation/fiber/cabinet_locations_sample.csv \
  --from-cabinet A-14 \
  --to-cabinet B-22 \
  --route-height-ft 10 \
  --turns 3
```

### CSV columns

Required:

- `cabinet_id`
- `x_ft`
- `y_ft`

Optional:

- `elevation_ft`
- `entry_height_ft`

---

## Usage: dcTrack API Mode

```bash
fiber-run-estimator \
  --dctrack-api-url https://dctrack.example.com/api/cabinets \
  --from-cabinet A-14 \
  --to-cabinet B-22 \
  --dctrack-token-env DCTRACK_API_TOKEN \
  --dctrack-data-path data.items \
  --field-cabinet-id name \
  --field-x x \
  --field-y y \
  --field-elevation z \
  --field-entry-height entry
```

Set token in environment before running:

```bash
export DCTRACK_API_TOKEN="your_token_here"
```

PowerShell:

```powershell
$env:DCTRACK_API_TOKEN = "your_token_here"
```

---

## Notes

- Default auth header is `Authorization: Bearer <token>`.
- If your API uses a different header format, use:
  - `--dctrack-auth-header`
  - `--dctrack-auth-prefix`
- If your payload nesting is different, set `--dctrack-data-path`.

