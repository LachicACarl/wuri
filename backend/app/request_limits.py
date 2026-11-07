from __future__ import annotations

from typing import Any, Awaitable, Callable


class _RequestBodyTooLarge(Exception):
    pass


class RequestBodyLimitMiddleware:
    """Enforce a total ASGI request-body ceiling before multipart parsing."""

    def __init__(self, app, max_body_bytes: int):
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive.")
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                declared_length = int(raw_length)
            except (TypeError, ValueError):
                declared_length = None
            if declared_length is not None and declared_length > self.max_body_bytes:
                await self._reject(send)
                return

        received_bytes = 0

        async def limited_receive():
            nonlocal received_bytes
            message = await receive()
            if message.get("type") == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_body_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            await self._reject(send)

    @staticmethod
    async def _reject(send):
        body = b'{"detail":"Request body exceeds the configured limit."}'
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": body})
