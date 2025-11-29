from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from openrsvp_cli.config import Settings


class NetworkError(Exception):
    """Raised when a network issue prevents contacting the API."""

    def __init__(self, message: str):
        super().__init__(message)


class APIError(Exception):
    """Raised when the API returns a non-success HTTP status."""

    def __init__(self, status_code: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AuthError(APIError):
    """Raised on authentication or authorization failures."""

    def __init__(self, status_code: int, message: str):
        super().__init__(status_code, message)


class APIClient:
    """Thin async HTTP client that injects base URL and auth headers."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "APIClient":
        headers: Dict[str, str] = {}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"

        self._client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            headers=headers,
            timeout=httpx.Timeout(10.0, connect=10.0),
        )
        return self

    async def __aexit__(self, *exc_info: Any) -> None:  # type: ignore[override]
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self._client is None:
            raise RuntimeError("APIClient must be used within an async context manager")

        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise NetworkError(
                f"Network error contacting {self.settings.base_url}: {exc}"  # pragma: no cover - runtime error path
            ) from exc

        if response.status_code in (401, 403):
            raise AuthError(
                response.status_code,
                "Authentication failed. Provide a valid token via --token, OPENRSVP_TOKEN, or ~/.config/openrsvp/config.toml.",
            )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.is_error:
            message = payload if isinstance(payload, str) else payload or response.text
            raise APIError(response.status_code, str(message), payload)

        return payload

    async def get(self, path: str, **params: Any) -> Any:
        return await self._request("GET", path, params=params or None)

    async def post(self, path: str, json: Any | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    async def patch(self, path: str, json: Any | None = None) -> Any:
        return await self._request("PATCH", path, json=json)
