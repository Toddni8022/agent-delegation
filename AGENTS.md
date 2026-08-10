# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Pure Python library (no web server, no database, no Docker) for async task delegation with priority queues and agent routing. See `README.md` for full API reference.

### Development commands

| Action | Command |
|---|---|
| Install (dev) | `pip install -e ".[dev]"` |
| Tests | `pytest` (48 tests, all async via `asyncio_mode = auto` in `pytest.ini`) |
| Format check | `black --check agent_delegation/ tests/ examples/` |
| Type check | `mypy agent_delegation/` |
| Run example | `python3 examples/basic_usage.py` |

### Non-obvious notes

- The system Python is `python3` (3.12). There is no `python` alias; always use `python3`.
- `pip install -e ".[dev]"` installs to `~/.local/bin` (user-level). Ensure `$HOME/.local/bin` is on `PATH` for `pytest`, `black`, `mypy` to be found.
- `black --check` reports 14 files needing reformatting — this is the existing state of the repo, not a regression.
- `mypy` reports 12 type errors — also pre-existing. Do not treat these as blockers.
- No external services, databases, or Docker needed. Everything runs in-process with `asyncio`.
