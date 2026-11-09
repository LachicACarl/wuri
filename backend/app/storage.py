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

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if candidate.parent != self.root.resolve():
            raise ValueError("Invalid storage key.")
        return candidate

    def stage_delete(self, key: str) -> str | None:
        """Atomically hide a file before its database record is removed."""
        candidate = self._path(key)
        if not candidate.exists():
            return None
        staged_key = f".wuri-delete-{uuid.uuid4().hex}"
        os.replace(candidate, self._path(staged_key))
        return staged_key

    def restore_staged_delete(self, staged_key: str, original_key: str):
        """Restore a staged file when the database deletion does not commit."""
        staged = self._path(staged_key)
        original = self._path(original_key)
        if staged.exists():
            if original.exists():
                raise FileExistsError("Original storage object already exists.")
            os.replace(staged, original)

    def finalize_staged_delete(self, staged_key: str):
        self._path(staged_key).unlink(missing_ok=True)

    def delete_staged(self, key: str):
        """Delete only an object created by the staged-delete protocol."""
        prefix = ".wuri-delete-"
        suffix = key[len(prefix):] if isinstance(key, str) and key.startswith(prefix) else ""
        if len(suffix) != 32 or any(c not in "0123456789abcdef" for c in suffix):
            raise ValueError("Invalid staged storage key.")
        self._path(key).unlink(missing_ok=True)

    def delete(self, key: str):
        self._path(key).unlink(missing_ok=True)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()
