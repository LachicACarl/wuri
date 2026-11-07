import hashlib
import os
from pathlib import Path
import tempfile
import uuid


class PrivateStorage:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.getenv("WURI_STORAGE_PATH") or Path(__file__).resolve().parents[1] / "private")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, extension: str) -> tuple[str, str]:
        key = f"{uuid.uuid4()}{extension}"
        destination = self.root / key
        checksum = hashlib.sha256(content).hexdigest()
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".wuri-upload-", suffix=".tmp", dir=self.root
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, destination)
        except Exception:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return key, checksum

    def delete(self, key: str):
        candidate = (self.root / key).resolve()
        if candidate.parent != self.root.resolve():
            raise ValueError("Invalid storage key.")
        candidate.unlink(missing_ok=True)

    def read(self, key: str) -> bytes:
        candidate = (self.root / key).resolve()
        if candidate.parent != self.root.resolve():
            raise ValueError("Invalid storage key.")
        return candidate.read_bytes()
