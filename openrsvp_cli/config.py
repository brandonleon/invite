from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:  # Python 3.10 compatibility
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib

CONFIG_PATH = Path.home() / ".openrsvp" / "config.toml"


def _read_config_file(path: Path = CONFIG_PATH) -> Dict[str, Optional[str]]:
    """Load configuration values from the TOML file if it exists."""
    if not path.exists():
        return {}

    try:
        with path.open("rb") as fh:
            raw: Dict[str, Any] = tomllib.load(fh)
    except Exception:
        # Gracefully ignore malformed configs instead of crashing.
        return {}

    # Allow either a top-level table or a named [openrsvp] section.
    config_section: Dict[str, Any] = raw.get("openrsvp", raw) if isinstance(raw, dict) else {}
    base_url = config_section.get("base_url")
    token = config_section.get("token")
    default_channel = config_section.get("default_channel")

    return {
        "base_url": str(base_url) if base_url is not None else None,
        "token": str(token) if token is not None else None,
        "default_channel": str(default_channel) if default_channel is not None else None,
    }


@dataclass
class Settings:
    """Resolved configuration for the CLI."""

    base_url: str
    token: Optional[str]
    default_channel: Optional[str]
    output_json: bool = False
    quiet: bool = False


def load_settings(
    *,
    cli_base_url: Optional[str] = None,
    cli_token: Optional[str] = None,
    cli_default_channel: Optional[str] = None,
    output_json: bool = False,
    quiet: bool = False,
) -> Settings:
    """Merge configuration values using CLI > env vars > config file precedence."""

    file_config = _read_config_file()
    env_config = {
        "base_url": os.getenv("OPENRSVP_BASE_URL"),
        "token": os.getenv("OPENRSVP_TOKEN"),
        "default_channel": os.getenv("OPENRSVP_DEFAULT_CHANNEL"),
    }

    base_url = (
        cli_base_url
        or env_config.get("base_url")
        or file_config.get("base_url")
        or "http://localhost:8000"
    )

    token = cli_token or env_config.get("token") or file_config.get("token")
    default_channel = (
        cli_default_channel
        or env_config.get("default_channel")
        or file_config.get("default_channel")
    )

    # Normalize URLs to avoid accidental double slashes.
    base_url = base_url.rstrip("/")

    return Settings(
        base_url=base_url,
        token=token,
        default_channel=default_channel,
        output_json=output_json,
        quiet=quiet,
    )
