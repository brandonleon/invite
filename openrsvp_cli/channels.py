from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import typer
from rich.console import Console
from rich.table import Table

from openrsvp_cli.client import APIClient, APIError, AuthError, NetworkError
from openrsvp_cli.config import Settings
from openrsvp_cli.utils import run_async_command

console = Console()

channels_app = typer.Typer(help="Manage channels.", no_args_is_help=True)


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


def _render_channels_table(channels: Iterable[Mapping[str, Any]]) -> Table:
    table = Table(title="Channels", expand=True)
    table.add_column("Name", style="cyan")
    table.add_column("Visibility", style="yellow")
    table.add_column("Invite Code", style="magenta")

    for channel in channels:
        table.add_row(
            str(channel.get("name", "")),
            str(channel.get("visibility", "")),
            str(channel.get("invite_code", "")),
        )
    return table


def _render_channel_detail(channel: Mapping[str, Any]) -> Table:
    table = Table(title="Channel", expand=True, show_lines=True)
    for key in ["name", "visibility", "invite_code", "description"]:
        table.add_row(key, str(channel.get(key, "")))
    return table


@channels_app.command("list")
@run_async_command
async def list_channels(ctx: typer.Context) -> None:
    """List all channels."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.get("/api/v1/channels")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        if isinstance(data, list):
            console.print(_render_channels_table(data))
        else:
            console.print(_render_channels_table([data]))


@channels_app.command("create")
@run_async_command
async def create_channel(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", help="Channel name."),
    visibility: str = typer.Option(
        ...,
        "--visibility",
        help="Channel visibility (public/private).",
        case_sensitive=False,
        callback=lambda v: v.lower() if v else v,
    ),
    invite_code: Optional[str] = typer.Option(None, "--invite-code", help="Optional invite code."),
) -> None:
    """Create a new channel."""

    settings = _get_settings(ctx)
    if visibility not in {"public", "private"}:
        raise typer.BadParameter("--visibility must be 'public' or 'private'.")

    payload = {
        "name": name,
        "visibility": visibility,
        "invite_code": invite_code,
    }

    try:
        async with APIClient(settings) as client:
            data = await client.post("/api/v1/channels", json=payload)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        console.print(_render_channel_detail(data))
        if not settings.quiet:
            console.print("[green]Channel created.[/green]")


@channels_app.command("show")
@run_async_command
async def show_channel(ctx: typer.Context, channel_name: str = typer.Argument(..., help="Channel name.")) -> None:
    """Show details for a single channel."""

    settings = _get_settings(ctx)
    try:
        async with APIClient(settings) as client:
            data = await client.get(f"/api/v1/channels/{channel_name}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, settings)
        return

    if settings.output_json:
        console.print_json(data=data)
    else:
        console.print(_render_channel_detail(data))
