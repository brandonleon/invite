from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import typer
from rich.console import Console
from rich.table import Table

from openrsvp_cli.client import APIClient, APIError, AuthError, NetworkError
from openrsvp_cli.config import Settings
from openrsvp_cli.utils import run_async_command

console = Console()

rsvps_app = typer.Typer(help="Manage RSVPs for events.", no_args_is_help=True)


def _get_settings(ctx: typer.Context) -> Settings:
    settings = ctx.obj
    if not isinstance(settings, Settings):
        raise typer.BadParameter("Configuration was not initialized. Run through main CLI entry.")
    return settings


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


def _render_rsvps_table(rsvps: Iterable[Mapping[str, Any]]) -> Table:
    table = Table(title="RSVPs", expand=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Email", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Guests", style="magenta")

    for rsvp in rsvps:
        table.add_row(
            str(rsvp.get("id", "")),
            str(rsvp.get("name", "")),
            str(rsvp.get("email", "")),
            str(rsvp.get("status", "")),
            str(rsvp.get("guests", "")),
        )
    return table


def _render_rsvp_detail(rsvp: Mapping[str, Any]) -> Table:
    table = Table(title="RSVP", expand=True, show_lines=True)
    for key in ["id", "event_id", "name", "email", "status", "guests", "note"]:
        table.add_row(key, str(rsvp.get(key, "")))
    return table


@rsvps_app.command("create")
@run_async_command
async def create_rsvp(
    ctx: typer.Context,
    event_id: str = typer.Argument(..., help="Event ID for the RSVP."),
    name: str = typer.Option(..., "--name", help="Name of the attendee."),
    email: str = typer.Option(..., "--email", help="Email of the attendee."),
    guests: int = typer.Option(1, "--guests", help="Number of guests including the requester."),
    note: Optional[str] = typer.Option(None, "--note", help="Optional note for the host."),
) -> None:
    """Create an RSVP for an event."""

    settings = _get_settings(ctx)
    payload = {
        "event_id": event_id,
        "name": name,
        "email": email,
        "guests": guests,
        "note": note,
    }

    try:
        async with APIClient(settings) as client:
            data = await client.post("/api/v1/rsvps", json=payload)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        console.print(_render_rsvp_detail(data))
        if not settings.quiet:
            console.print("[green]RSVP created.[/green]")


@rsvps_app.command("list")
@run_async_command
async def list_rsvps(ctx: typer.Context, event_id: str = typer.Argument(..., help="Event ID.")) -> None:
    """List RSVPs for a specific event."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.get(f"/api/v1/events/{event_id}/rsvps")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        if isinstance(data, list):
            console.print(_render_rsvps_table(data))
        else:
            console.print(_render_rsvps_table([data]))


@rsvps_app.command("approve")
@run_async_command
async def approve_rsvp(ctx: typer.Context, rsvp_id: str = typer.Argument(..., help="RSVP ID.")) -> None:
    """Approve an RSVP."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.post(f"/api/v1/rsvps/{rsvp_id}/approve")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    elif not settings.quiet:
        console.print(f"[green]RSVP {rsvp_id} approved.[/green]")


@rsvps_app.command("reject")
@run_async_command
async def reject_rsvp(
    ctx: typer.Context,
    rsvp_id: str = typer.Argument(..., help="RSVP ID."),
    reason: str = typer.Option(..., "--reason", help="Reason for rejection."),
) -> None:
    """Reject an RSVP with a provided reason."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.post(f"/api/v1/rsvps/{rsvp_id}/reject", json={"reason": reason})
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    elif not settings.quiet:
        console.print(f"[green]RSVP {rsvp_id} rejected.[/green]")


@rsvps_app.command("delete")
@run_async_command
async def delete_rsvp(ctx: typer.Context, rsvp_id: str = typer.Argument(..., help="RSVP ID.")) -> None:
    """Delete an RSVP."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.delete(f"/api/v1/rsvps/{rsvp_id}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    elif not settings.quiet:
        console.print(f"[green]RSVP {rsvp_id} deleted.[/green]")
