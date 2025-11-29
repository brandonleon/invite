from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from openrsvp_cli.config import CONFIG_PATH, save_base_url

console = Console()

config_app = typer.Typer(help="Manage OpenRSVP CLI configuration.", no_args_is_help=True)


@config_app.command("set-base-url")
def set_base_url(
    base_url_arg: Optional[str] = typer.Argument(
        None,
        help="Base URL to write into ~/.config/openrsvp/config.toml (positional).",
    ),
    base_url_option: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-b",
        help="Base URL to write into ~/.config/openrsvp/config.toml (option).",
    ),
) -> None:
    """Persist the provided base URL to the config file."""

    base_url = base_url_arg or base_url_option or "http://localhost:8000"

    try:
        path = save_base_url(base_url)
    except Exception as exc:  # noqa: BLE001 - surface to the user
        console.print(f"[red]Failed to update config: {exc}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Saved base_url to {path}[/green]")
