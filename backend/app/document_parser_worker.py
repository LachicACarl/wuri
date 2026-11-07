from __future__ import annotations

import json
import os
import sys


MAX_WORKER_INPUT_BYTES = 25 * 1024 * 1024
WORKER_MEMORY_BYTES = 1024 * 1024 * 1024
WORKER_CPU_SECONDS = 20


def _apply_limits() -> bool:
    if os.name != "posix":
        return False
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (WORKER_CPU_SECONDS, WORKER_CPU_SECONDS + 1))
        resource.setrlimit(resource.RLIMIT_AS, (WORKER_MEMORY_BYTES, WORKER_MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        return True
    except (ImportError, AttributeError, OSError, ValueError):
        return False


def main() -> int:
    if not _apply_limits():
        sys.stdout.write(json.dumps({
            "error_type": "WorkerLimitsUnavailable",
            "error": "Parser worker resource limits are unavailable.",
        }))
        return 70

    filename = sys.argv[1] if len(sys.argv) > 1 else ""
    content = sys.stdin.buffer.read(MAX_WORKER_INPUT_BYTES + 1)
    if len(content) > MAX_WORKER_INPUT_BYTES:
        sys.stdout.write(json.dumps({
            "error_type": "ValueError",
            "error": "Document exceeds the parser worker input limit.",
        }))
        return 2

    try:
        from dataclasses import asdict
        from app.document_processing import extract_blocks

        blocks = extract_blocks(filename, content)
        sys.stdout.write(json.dumps({"blocks": [asdict(block) for block in blocks]}))
        return 0
    except ValueError as error:
        sys.stdout.write(json.dumps({
            "error_type": "ValueError",
            "error": str(error),
        }))
        return 2
    except Exception:
        sys.stdout.write(json.dumps({
            "error_type": "ParserError",
            "error": "The document parser failed.",
        }))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
