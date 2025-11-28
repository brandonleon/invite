# Invite CLI

Typer-based CLI for the OpenRSVP HTTP API described in `CLI_API.md`. Commands print JSON responses for easy piping or inspection.

## Running
- Install deps with uv (a virtualenv is created automatically): `uv sync`
- Set optional env vars:
  - `INVITE_API_BASE_URL` (overrides config/default base URL)
  - `INVITE_ADMIN_TOKEN` (default admin token for admin commands)
- Use the `invite` entrypoint: `uv run invite --help`

### Config file
- Default base URL: `https://openrsvp.kaotic.cc`
- To persist a different base URL (e.g., self-hosting), write `~/.config/invite/config.toml`:
  - `uv run invite configure --base-url https://your-host`
  - Layout: `base_url = "https://your-host"`
  - `--base-url` flag or `INVITE_API_BASE_URL` will override the config file at runtime.

## Commands
- Create an event  
  `uv run invite create-event "My Event" --start-time 2025-01-01T18:00:00 --location "Main Hall" --tz-offset -300 --require-approval`  
  Prints the event plus the admin token and admin URL.
- Show event details (public)  
  `uv run invite show-event <event_id>`
- List RSVPs (admin)  
  `uv run invite rsvps <event_id> --admin-token <token>` (token may also come from `INVITE_ADMIN_TOKEN`)
- Show public feed (upcoming)  
  `uv run invite public-events` (uses the public channel; pass `--channel <slug>` to target another channel, `--page` for pagination)

Field meanings and allowed shapes follow `CLI_API.md`.
