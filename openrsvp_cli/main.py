from __future__ import annotations

import typer
from rich.console import Console

from openrsvp_cli.channels import channels_app
from openrsvp_cli.config import Settings, load_settings
from openrsvp_cli.config_cli import config_app
from openrsvp_cli.events import events_app
from openrsvp_cli.rsvps import rsvps_app

console = Console()

app = typer.Typer(
    help="CLI for interacting with the OpenRSVP server.",
    no_args_is_help=True,
)


@app.callback()
def main(  # type: ignore[override]
    ctx: typer.Context,
    base_url: str = typer.Option(
        None,
        "--base-url",
        help="Base URL for the OpenRSVP server (overrides env/config).",
    ),
    token: str = typer.Option(
        None,
        "--token",
        help="Authentication token (overrides env/config).",
    ),
    default_channel: str = typer.Option(
        None,
        "--default-channel",
        help="Default channel to target when omitted in commands.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Return responses as raw JSON for scripting.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Reduce noisy output for scripting contexts.",
    ),
) -> None:
    """Load configuration with correct precedence and stash it in the context."""

    settings = load_settings(
        cli_base_url=base_url,
        cli_token=token,
        cli_default_channel=default_channel,
        output_json=output_json,
        quiet=quiet,
    )
    ctx.obj = settings


app.add_typer(events_app, name="events")
app.add_typer(rsvps_app, name="rsvps")
app.add_typer(channels_app, name="channels")
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
