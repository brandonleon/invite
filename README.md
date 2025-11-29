# Invite (OpenRSVP CLI)

Async Typer CLI for interacting with the OpenRSVP FastAPI backend. Everything runs with `uv` and can be installed directly from git to expose an `invite` command.

## Quickstart
- Install deps: `uv sync`
- Run help: `uv run invite --help` (aliases: `uv run openrsvp_cli --help`, `uv run openrsvp-cli --help`, `uv run python -m openrsvp_cli`, or `uv run main.py`)
- Install tool from git: `uv tool install git+https://your.git.repo/url#egg=invite`

## Configuration
Values resolve in order CLI flag > env var > `~/.config/openrsvp/config.toml`.
- Env vars: `OPENRSVP_BASE_URL`, `OPENRSVP_TOKEN`, `OPENRSVP_DEFAULT_CHANNEL`
- Config file example (stored in `~/.config/openrsvp/config.toml`):
  ```toml
  base_url = "https://openrsvp.example.com"
  token = "YOUR_TOKEN"
  default_channel = "general"
  ```
- Update the stored base URL from the CLI: `invite config set-base-url https://openrsvp.example.com` (or `--base-url/ -b ...`; defaults to `http://localhost:8000`).

Global flags: `--base-url`, `--token`, `--default-channel`, `--json`, `--quiet`.

## Commands
All commands are async; Typer handles event loop automatically.
- Events: `invite events list`, `invite events create`, `invite events show <id>`, `invite events delete <id>`
- RSVPs: `invite rsvps list <event_id>`, `invite rsvps create <event_id>`, `invite rsvps approve <rsvp_id>`, `invite rsvps reject <rsvp_id> --reason`, `invite rsvps delete <rsvp_id>`
- Channels: `invite channels list`, `invite channels create`, `invite channels show <name>`

Use `--json` for raw JSON output or `--quiet` to suppress success chatter. Rich tables render by default.
