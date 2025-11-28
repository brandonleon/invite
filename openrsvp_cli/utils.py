from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable, TypeVar

Result = TypeVar("Result")


def run_async_command(func: Callable[..., Awaitable[Result]]) -> Callable[..., Result]:
    """Turn an async Typer callback into a sync function so Click can execute it."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Result:
        return asyncio.run(func(*args, **kwargs))

    return wrapper
