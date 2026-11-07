import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.storage import PrivateStorage


class PrivateStorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.storage = PrivateStorage(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def test_save_writes_content_and_returns_sha256(self):
        payload = b"synthetic evidence"
        key, checksum = self.storage.save(payload, ".txt")

        self.assertEqual(self.storage.read(key), payload)
        self.assertEqual(checksum, hashlib.sha256(payload).hexdigest())
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_failed_atomic_replace_removes_temporary_file(self):
        with patch("app.storage.os.replace", side_effect=OSError("synthetic replace failure")):
            with self.assertRaisesRegex(OSError, "synthetic replace failure"):
                self.storage.save(b"synthetic evidence", ".txt")

        self.assertEqual(list(self.root.iterdir()), [])

    def test_storage_rejects_path_traversal_keys(self):
        with self.assertRaisesRegex(ValueError, "Invalid storage key"):
            self.storage.read("../outside.txt")
        with self.assertRaisesRegex(ValueError, "Invalid storage key"):
            self.storage.delete("../outside.txt")


if __name__ == "__main__":
    unittest.main()
