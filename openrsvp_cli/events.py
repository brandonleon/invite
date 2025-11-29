from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, List, Mapping

import typer
from rich.console import Console
from rich.table import Table

from openrsvp_cli.client import APIClient, APIError, AuthError, NetworkError
from openrsvp_cli.config import Settings
from openrsvp_cli.utils import run_async_command

console = Console()

events_app = typer.Typer(help="Manage OpenRSVP events.", no_args_is_help=True)


def _get_settings(ctx: typer.Context) -> Settings:
    settings = ctx.obj
    if not isinstance(settings, Settings):
        raise typer.BadParameter("Configuration was not initialized. Run through main CLI entry.")
    return settings


def _validate_datetime(value: str) -> str:
    """Ensure provided date/time strings are ISO-8601 parseable."""
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - simple validation path
        raise typer.BadParameter("Date/time must be ISO-8601, e.g. 2024-03-01T10:00:00") from exc
    return value


def _handle_error(exc: Exception, settings: Settings) -> None:
    if isinstance(exc, AuthError):
        console.print(f"[red]{exc}[/red]")
    elif isinstance(exc, NetworkError):
        console.print(f"[red]{exc}[/red]")
    elif isinstance(exc, APIError):
        console.print(f"[red]API error ({exc.status_code}): {exc}[/red]")
        if settings.output_json and exc.payload:
            console.print_json(data=exc.payload)
    else:  # pragma: no cover - defensive
        console.print(f"[red]Unexpected error: {exc}[/red]")
    raise typer.Exit(code=1)


def _render_events_table(events: Iterable[Mapping[str, Any]]) -> Table:
    table = Table(title="Events", expand=True)
    table.add_column("ID", style="cyan", overflow="fold")
    table.add_column("Title", style="white", overflow="fold")
    table.add_column("Start", style="green")
    table.add_column("End", style="green")
    table.add_column("Channel", style="magenta")
    table.add_column("Private", style="yellow")
    table.add_column("Approval", style="yellow")

    for event in events:
        channel_value = event.get("channel")
        if isinstance(channel_value, dict):
            channel_value = channel_value.get("slug") or channel_value.get("name") or channel_value.get("id")

        table.add_row(
            str(event.get("id", "")),
            str(event.get("title", "")),
            str(event.get("start_time") or event.get("start") or ""),
            str(event.get("end_time") or event.get("end") or ""),
            str(channel_value or ""),
            "yes" if event.get("is_private") else "no",
            "yes" if event.get("admin_approval_required") or event.get("requires_approval") else "no",
        )
    return table


def _render_event_detail(event: Mapping[str, Any]) -> Table:
    table = Table(title="Event", expand=True, show_lines=True)
    channel_value = event.get("channel")
    if isinstance(channel_value, dict):
        channel_value = channel_value.get("slug") or channel_value.get("name") or channel_value.get("id")

    rows = {
        "id": event.get("id", ""),
        "title": event.get("title", ""),
        "description": event.get("description", ""),
        "start_time": event.get("start_time") or event.get("start") or "",
        "end_time": event.get("end_time") or event.get("end") or "",
        "location": event.get("location", ""),
        "channel": channel_value or "",
        "is_private": event.get("is_private", ""),
        "admin_approval_required": event.get("admin_approval_required") or event.get("requires_approval") or "",
        "public_link": (event.get("links") or {}).get("public", ""),
    }
    for key, value in rows.items():
        table.add_row(key, str(value))
    return table


def _extract_events_payload(data: Any) -> List[Mapping[str, Any]]:
    """Normalize various API list responses into a list of events."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("events", "items", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


@events_app.command("list")
@run_async_command
async def list_events(
    ctx: typer.Context,
    channel: str = typer.Option(None, "--channel", help="Filter by channel."),
    public_only: bool = typer.Option(
        False, "--public-only/--all", help="Show only public events when set."
    ),
) -> None:
    """List events with optional channel and visibility filters."""

    settings = _get_settings(ctx)
    target_channel = channel or settings.default_channel

    try:
        async with APIClient(settings) as client:
            if target_channel:
                data = await client.get(f"/api/v1/channels/{target_channel}")
            elif settings.token:
                data = await client.get(f"/admin/{settings.token}/events")
            else:
                data = await client.get("/api/v1/events")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        events = _extract_events_payload(data)
        if public_only:
            events = [event for event in events if not event.get("is_private")]

        if events:
            console.print(_render_events_table(events))
        else:
            console.print("[yellow]No events found.[/yellow]")


@events_app.command("create")
@run_async_command
async def create_event(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", help="Event title."),
    description: str = typer.Option(..., "--description", help="Event description."),
    start: str = typer.Option(..., "--start", callback=_validate_datetime, help="Start time (ISO-8601)."),
    end: str = typer.Option(..., "--end", callback=_validate_datetime, help="End time (ISO-8601)."),
    channel: str = typer.Option(..., "--channel", help="Channel name."),
    is_private: bool = typer.Option(
        False,
        "--is-private/--no-is-private",
        help="Whether the event is private.",
    ),
    requires_approval: bool = typer.Option(
        False,
        "--requires-approval/--no-requires-approval",
        help="Require approval for RSVPs.",
    ),
) -> None:
    """Create a new event."""

    settings = _get_settings(ctx)
    payload = {
        "title": title,
        "description": description,
        "start_time": start,
        "end_time": end,
        "channel_name": channel,
        "is_private": is_private,
        "admin_approval_required": requires_approval,
    }

    try:
        async with APIClient(settings) as client:
            data = await client.post("/api/v1/events", json=payload)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        console.print(_render_event_detail(data))
        if not settings.quiet:
            console.print("[green]Event created successfully.[/green]")


@events_app.command("show")
@run_async_command
async def show_event(ctx: typer.Context, event_id: str = typer.Argument(..., help="Event ID.")) -> None:
    """Show details for a single event."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.get(f"/api/v1/events/{event_id}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    event = data.get("event") if isinstance(data, dict) and "event" in data else data

    if settings.output_json:
        console.print_json(data=event)
    else:
        console.print(_render_event_detail(event or {}))


@events_app.command("delete")
@run_async_command
async def delete_event(ctx: typer.Context, event_id: str = typer.Argument(..., help="Event ID.")) -> None:
    """Delete an event by ID."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.delete(f"/api/v1/events/{event_id}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    elif not settings.quiet:
        console.print(f"[green]Deleted event {event_id}.[/green]")
