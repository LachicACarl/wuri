import asyncio
import unittest

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.request_limits import RequestBodyLimitMiddleware


class RequestBodyLimitTests(unittest.TestCase):
    def test_declared_oversized_body_is_rejected_before_application(self):
        called = False

        async def application(scope, receive, send):
            nonlocal called
            called = True

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"12345", "more_body": False}

        async def send(message):
            messages.append(message)

        middleware = RequestBodyLimitMiddleware(application, max_body_bytes=4)
        asyncio.run(middleware(
            {"type": "http", "headers": [(b"content-length", b"5")]},
            receive,
            send,
        ))

        self.assertFalse(called)
        self.assertEqual(messages[0]["status"], 413)

    def test_streamed_oversized_body_is_rejected(self):
        called = False

        async def application(scope, receive, send):
            nonlocal called
            called = True
            await receive()

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"12345", "more_body": False}

        async def send(message):
            messages.append(message)

        middleware = RequestBodyLimitMiddleware(application, max_body_bytes=4)
        asyncio.run(middleware(
            {"type": "http", "headers": []},
            receive,
            send,
        ))

        self.assertTrue(called)
        self.assertEqual(messages[0]["status"], 413)
        self.assertIn(b"configured limit", messages[1]["body"])

    def test_cors_allowlist_wraps_request_limit_and_blocks_untrusted_origins(self):
        app = FastAPI()

        @app.post("/body")
        async def body(request: Request):
            await request.body()
            return {"ok": True}

        # The last Starlette middleware registered wraps earlier middleware.
        app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=4)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://trusted.example"],
            allow_credentials=True,
            allow_methods=["POST"],
            allow_headers=["Content-Type"],
        )
        client = TestClient(app)

        trusted = client.post(
            "/body", content=b"12345", headers={"Origin": "https://trusted.example"}
        )
        self.assertEqual(trusted.status_code, 413)
        self.assertEqual(trusted.headers.get("access-control-allow-origin"), "https://trusted.example")
        self.assertEqual(trusted.headers.get("access-control-allow-credentials"), "true")

        untrusted = client.post(
            "/body", content=b"12345", headers={"Origin": "https://attacker.example"}
        )
        self.assertEqual(untrusted.status_code, 413)
        self.assertIsNone(untrusted.headers.get("access-control-allow-origin"))

    def test_non_http_scope_passes_through_without_body_inspection(self):
        called = False

        async def application(scope, receive, send):
            nonlocal called
            called = True

        async def receive():
            return {"type": "lifespan.startup"}

        async def send(message):
            pass

        middleware = RequestBodyLimitMiddleware(application, max_body_bytes=4)
        asyncio.run(middleware({"type": "lifespan"}, receive, send))
        self.assertTrue(called)


if __name__ == "__main__":
    unittest.main()
