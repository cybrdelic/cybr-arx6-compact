"""Regression checks for exact, non-overwriting native-cache restoration."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HELPER = Path(__file__).resolve().parents[1] / "tools" / "restore_native_cache.py"
spec = importlib.util.spec_from_file_location("restore_native_cache", HELPER)
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)

def digest(data):
    return hashlib.sha256(data).hexdigest()

class RestoreNativeCacheTests(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).resolve().parent
        self.temp = tempfile.TemporaryDirectory(prefix="cache-restore-test-", dir=test_root)
        self.root = Path(self.temp.name).resolve()
        assert self.root.parent == test_root
        self.addCleanup(self.temp.cleanup)
        patch = mock.patch.object(restore, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.data = b"exact native triangle data\x00\x01\x02" * 10
        compressed = gzip.compress(self.data, mtime=0)
        self.dest = self.root / "assets/native.bin"
        self.dest.parent.mkdir()
        self.part = self.root / "assets/native.bin.gz.part"
        self.part.write_bytes(compressed)
        metadata = {"target": "assets/native.bin", "bytes": len(self.data),
                    "sha256": digest(self.data), "gzip_bytes": len(compressed),
                    "gzip_sha256": digest(compressed),
                    "parts": [{"path": "assets/native.bin.gz.part",
                               "bytes": len(compressed), "sha256": digest(compressed)}]}
        (self.root / "assets/native-cache-parts.json").write_text(json.dumps(metadata))

    def assert_no_temporary_files(self):
        self.assertEqual(list(self.dest.parent.glob(".native-cache-*")), [])

    def test_restores_exact_bytes_on_current_filesystem(self):
        restore.main()
        self.assertEqual(self.dest.read_bytes(), self.data)
        self.assert_no_temporary_files()

    def test_matching_destination_is_idempotent(self):
        self.dest.write_bytes(self.data)
        before = self.dest.stat().st_mtime_ns
        restore.main()
        self.assertEqual(self.dest.read_bytes(), self.data)
        self.assertEqual(self.dest.stat().st_mtime_ns, before)
        self.assert_no_temporary_files()

    def test_different_destination_is_preserved(self):
        original = b"existing caller-owned data"
        self.dest.write_bytes(original)
        with self.assertRaises(SystemExit):
            restore.main()
        self.assertEqual(self.dest.read_bytes(), original)
        self.assert_no_temporary_files()

    def test_corrupt_part_cannot_publish(self):
        self.part.write_bytes(b"corrupt")
        with self.assertRaises(SystemExit):
            restore.main()
        self.assertFalse(self.dest.exists())
        self.assert_no_temporary_files()

    @unittest.skipUnless(os.name == "nt", "Windows rename no-overwrite semantics")
    def test_unsupported_link_race_preserves_winning_destination(self):
        original = b"concurrent publisher"
        def unsupported_link(source, destination):
            Path(destination).write_bytes(original)
            error = OSError("hard links unsupported")
            error.winerror = 1
            raise error
        with mock.patch.object(restore.os, "link", side_effect=unsupported_link):
            with self.assertRaises(FileExistsError):
                restore.main()
        self.assertEqual(self.dest.read_bytes(), original)
        self.assert_no_temporary_files()

    @unittest.skipUnless(os.name == "nt", "Windows rename fallback")
    def test_successful_fallback_for_known_unsupported_errors(self):
        for code in (1, 50):
            with self.subTest(winerror=code):
                error = OSError("hard links unsupported")
                error.winerror = code
                with mock.patch.object(restore.os, "link", side_effect=error):
                    restore.main()
                self.assertEqual(digest(self.dest.read_bytes()), digest(self.data))
                self.assert_no_temporary_files()
                self.dest.unlink()

    def test_unrelated_link_failure_does_not_fall_back(self):
        error = OSError("access denied")
        error.winerror = 5
        with mock.patch.object(restore.os, "link", side_effect=error):
            with mock.patch.object(restore.os, "rename") as rename:
                with self.assertRaises(OSError):
                    restore.main()
                rename.assert_not_called()
        self.assertFalse(self.dest.exists())
        self.assert_no_temporary_files()

if __name__ == "__main__":
    unittest.main()
