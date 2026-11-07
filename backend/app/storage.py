import hashlib
import os
from pathlib import Path
import uuid


class PrivateStorage:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.getenv("WURI_STORAGE_PATH") or Path(__file__).resolve().parents[1] / "private")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, extension: str) -> tuple[str, str]:
        key = f"{uuid.uuid4()}{extension}"
        destination = self.root / key
        destination.write_bytes(content)
        return key, hashlib.sha256(content).hexdigest()

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
