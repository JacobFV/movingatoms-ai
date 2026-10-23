import tempfile
import unittest
from pathlib import Path
from minimal_seed import SOURCES, fetch

class SeedProvenanceTests(unittest.TestCase):
    def test_every_seed_and_license_is_immutably_pinned(self):
        for source in SOURCES:
            self.assertRegex(source['commit'],r'^[0-9a-f]{40}$')
            self.assertRegex(source['license_sha256'],r'^[0-9a-f]{64}$')
            for path,digest in source['files']:
                self.assertRegex(digest,r'^[0-9a-f]{64}$')
                self.assertTrue(path.endswith(('.rvt','.rte')))

    def test_cached_mismatch_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'seed';path.write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                fetch('https://example.invalid/never-fetched',path,'0'*64)
            self.assertEqual(path.read_bytes(),b'wrong')
