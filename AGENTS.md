# Repository Guidelines

## Project Structure & Module Organization
- CLI source lives in `openrsvp_cli/`. Entry point is `openrsvp_cli/main.py` (also exposed via `main.py` at repo root for `python main.py`).
- Command groups sit in `openrsvp_cli/events.py`, `openrsvp_cli/rsvps.py`, `openrsvp_cli/channels.py`, and `openrsvp_cli/config_cli.py`; shared helpers are in `openrsvp_cli/utils.py`.
- HTTP client and configuration helpers are in `openrsvp_cli/client.py` and `openrsvp_cli/config.py`. Persistent config defaults to `~/.config/openrsvp/config.toml`.
- Packaging metadata and script bindings live in `pyproject.toml`; dependency lock is `uv.lock`. No dedicated test directory yet.

## Build, Test, and Development Commands
- Install deps: `uv sync` (reads `pyproject.toml` and `uv.lock`).
- Run the CLI locally: `uv run invite --help` or `uv run main.py ...`.
- Use aliases for module execution when debugging: `uv run python -m openrsvp_cli`.
- Packaging entry points are defined under `[project.scripts]`; use `uv tool install .` to install the CLI globally from the repo.

## Coding Style & Naming Conventions
- Python 3.10+ with Typer and Rich; keep type hints and `from __future__ import annotations` at the top of new modules.
- Prefer `async` HTTP calls (matching `httpx` usage) and small, composable Typer commands. Keep option names descriptive and kebab-case (`--base-url`, `--default-channel`).
- 4-space indentation, double quotes for user-facing strings, and concise docstrings or inline comments only when non-obvious.
- Align output helpers with existing Rich table patterns; keep user-facing messaging quiet-friendly (`--json`, `--quiet` respected).

## Testing Guidelines
- No test suite is present yet; when adding one, use `pytest` and place files under `tests/` mirroring command modules.
- Name tests after behavior (e.g., `test_events_create_validates_payload`) and cover both JSON and quiet output paths.
- For manual checks, run representative commands against a dev OpenRSVP instance; rely on `--json` for scripting verification.

## Commit & Pull Request Guidelines
- Commit messages in this repo are short and imperative (e.g., “Add events list command”). Use scoped, descriptive subjects; avoid long bodies unless explaining rationale.
- Keep PRs focused on one area (command, config, or client). Include: summary of changes, manual test commands executed, and any API assumptions (base URL, token, channel).
- If you change config behavior, document precedence (flag > env > `~/.config/openrsvp/config.toml`) and update examples in `README.md`.
