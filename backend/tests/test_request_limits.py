import asyncio
import unittest

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
