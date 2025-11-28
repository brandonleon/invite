import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore

import httpx
import typer

DEFAULT_BASE_URL = "https://openrsvp.kaotic.cc"
CONFIG_PATH = Path.home() / ".config" / "invite" / "config.toml"

app = typer.Typer(
    add_completion=False,
    help="Interact with the OpenRSVP HTTP API.",
    no_args_is_help=True,  # show sub-commands when none are provided
)


def _load_config_base_url() -> Optional[str]:
    if not CONFIG_PATH.exists():
        return None

    try:
        with CONFIG_PATH.open("rb") as f:
            data = tomllib.load(f)
        base_url = data.get("base_url")
        return str(base_url) if base_url else None
    except Exception:
        return None


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _print_json(data: Dict[str, Any]) -> None:
    typer.echo(json.dumps(data, indent=2))


def _request(
    ctx: typer.Context,
    method: str,
    path: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json_payload: Optional[Dict[str, Any]] = None,
    echo: bool = True,
) -> Optional[Dict[str, Any]]:
    base_url: str = ctx.obj["base_url"]
    with httpx.Client(base_url=base_url, timeout=15) as client:
        response = client.request(method, path, headers=headers, json=json_payload)

    if response.status_code == 204:
        typer.secho("Success (204 No Content)", fg="green")
        return None

    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text}

    if response.is_success:
        if echo:
            if isinstance(data, dict):
                _print_json(data)
            else:
                typer.echo(json.dumps(data, indent=2))
        return data

    typer.secho(f"Request failed ({response.status_code})", fg="red")
    _print_json(data if isinstance(data, dict) else {"detail": data})
    raise typer.Exit(code=1)


def _resolve_admin_token(ctx: typer.Context, admin_token: Optional[str]) -> str:
    token = admin_token or ctx.obj.get("admin_token")
    if not token:
        typer.secho(
            "An admin token is required. Use --admin-token or set INVITE_ADMIN_TOKEN.",
            fg="red",
        )
        raise typer.Exit(code=1)
    return token


@app.command("configure")
def configure(
    base_url: str = typer.Option(
        ...,
        "--base-url",
        "-b",
        help="Base URL to store in the config file (e.g., https://openrsvp.kaotic.cc).",
    )
) -> None:
    """Write ~/.config/invite/config.toml with defaults."""
    normalized = _normalize_base_url(base_url)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(f'base_url = "{normalized}"\n', encoding="utf-8")
    typer.secho(f"Saved config to {CONFIG_PATH}", fg="green")


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        envvar="INVITE_API_BASE_URL",
        help="Base URL for the OpenRSVP API (no trailing slash). Overrides config file.",
    ),
    admin_token: Optional[str] = typer.Option(
        None,
        "--admin-token",
        "-a",
        envvar="INVITE_ADMIN_TOKEN",
        help="Default admin token used for admin-only commands.",
    ),
) -> None:
    """Configure shared options."""
    config_base_url = _load_config_base_url()
    effective_base = base_url or config_base_url or DEFAULT_BASE_URL
    ctx.obj = {"base_url": _normalize_base_url(effective_base), "admin_token": admin_token}


@app.command("create-event")
def create_event(
    ctx: typer.Context,
    title: str = typer.Argument(..., help="Title for the event."),
    start_time: str = typer.Option(
        ..., "--start-time", "-s", help="ISO8601 start time (e.g., 2024-01-01T18:00:00)."
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Optional description for the event."
    ),
    end_time: Optional[str] = typer.Option(
        None,
        "--end-time",
        help="Optional ISO8601 end time (must be after start).",
    ),
    timezone_offset_minutes: int = typer.Option(
        0,
        "--tz-offset",
        help="Minutes offset from UTC for the supplied times (default: 0).",
    ),
    location: Optional[str] = typer.Option(
        None, "--location", help="Location or venue description."
    ),
    channel_name: Optional[str] = typer.Option(
        None, "--channel-name", help="Channel name to associate to the event."
    ),
    channel_visibility: str = typer.Option(
        "public",
        "--channel-visibility",
        help="Channel visibility (public or private).",
        show_default=True,
    ),
    is_private: bool = typer.Option(
        False,
        "--private",
        help="Mark event RSVPs as private (still counted in totals).",
        show_default=True,
    ),
    admin_approval_required: bool = typer.Option(
        False,
        "--require-approval",
        help="Require admin approval for new RSVPs.",
        show_default=True,
    ),
) -> None:
    """Create a new event."""
    visibility_normalized = channel_visibility.lower()
    if visibility_normalized not in {"public", "private"}:
        raise typer.BadParameter("channel-visibility must be 'public' or 'private'.")

    payload: Dict[str, Any] = {
        "title": title,
        "start_time": start_time,
        "timezone_offset_minutes": timezone_offset_minutes,
        "channel_visibility": visibility_normalized,
        "is_private": is_private,
        "admin_approval_required": admin_approval_required,
    }

    if description:
        payload["description"] = description
    if end_time:
        payload["end_time"] = end_time
    if location:
        payload["location"] = location
    if channel_name is not None:
        payload["channel_name"] = channel_name

    data = _request(ctx, "POST", "/api/v1/events", json_payload=payload, echo=False)
    if not data:
        return

    admin_token = data.get("admin_token")
    event = data.get("event")

    if event:
        typer.secho("Event created:", fg="green")
        _print_json(event)

    if admin_token:
        typer.echo("")
        typer.secho("Admin token (save this):", fg="yellow")
        typer.echo(admin_token)
        admin_link = event.get("links", {}).get("admin") if isinstance(event, dict) else None
        if admin_link:
            typer.echo(f"Admin URL: {admin_link}")


@app.command("show-event")
def show_event(ctx: typer.Context, event_id: str = typer.Argument(..., help="Event ID to fetch.")) -> None:
    """Show public details for an event."""
    _request(ctx, "GET", f"/api/v1/events/{event_id}")


@app.command("rsvps")
def list_rsvps(
    ctx: typer.Context,
    event_id: str = typer.Argument(..., help="Event ID to list RSVPs for."),
    admin_token: Optional[str] = typer.Option(
        None,
        "--admin-token",
        "-a",
        envvar="INVITE_ADMIN_TOKEN",
        help="Admin token to authorize the RSVP listing.",
    ),
) -> None:
    """List RSVPs for an event (admin only)."""
    token = _resolve_admin_token(ctx, admin_token)
    headers = {"Authorization": f"Bearer {token}"}
    _request(ctx, "GET", f"/api/v1/events/{event_id}/rsvps", headers=headers)


def _collect_events_from_payload(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(data, dict):
        return []

    if isinstance(data.get("events"), list):
        return [e for e in data["events"] if isinstance(e, dict)]

    channel = data.get("channel")
    if isinstance(channel, dict) and isinstance(channel.get("events"), list):
        return [e for e in channel["events"] if isinstance(e, dict)]

    return []


def _parse_start_time(value: Any) -> datetime:
    if not isinstance(value, str):
        return datetime.max
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.max


@app.command("public-events")
def public_events(
    ctx: typer.Context,
    page: int = typer.Option(1, "--page", "-p", min=1, help="Page of the public feed to fetch."),
    channel_slug: str = typer.Option(
        "public",
        "--channel",
        "-c",
        help="Channel slug to query for events (default: public feed).",
        show_default=True,
    ),
) -> None:
    """Show public events sorted by upcoming start time."""
    data = _request(ctx, "GET", f"/api/v1/channels/{channel_slug}?page={page}")
    events = _collect_events_from_payload(data or {})

    if not events:
        typer.secho("No public events found.", fg="yellow")
        return

    events_sorted = sorted(events, key=lambda e: _parse_start_time(e.get("start_time")))

    typer.secho(f"Public events (channel: {channel_slug}, page {page}):", fg="green")
    for event in events_sorted:
        title = event.get("title", "(untitled)")
        eid = event.get("id", "unknown")
        start_time = event.get("start_time", "?")
        location = event.get("location")
        public_link = event.get("links", {}).get("public") if isinstance(event.get("links"), dict) else None

        line = f"- {start_time} | {title} (id: {eid})"
        if location:
            line += f" @ {location}"
        typer.echo(line)
        if public_link:
            typer.echo(f"  public: {public_link}")


if __name__ == "__main__":
    app()
