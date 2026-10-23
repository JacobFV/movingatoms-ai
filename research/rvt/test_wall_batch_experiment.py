import hashlib
from pathlib import Path
import tempfile
import unittest
from wall_batch_experiment import publish_checked


class BatchPublicationTests(unittest.TestCase):
    def test_mismatched_or_absent_evidence_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'staged.rvt';source.write_bytes(b'candidate')
            output=Path(directory)/'verified.rvt'
            for reports in ([],[{}],[{'candidate_sha256':'wrong'}]):
                with self.assertRaises(ValueError):publish_checked(source,output,reports)
                self.assertFalse(output.exists())
            good={'candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
            with self.assertRaises(ValueError):publish_checked(source,output,[good,{'candidate_sha256':'wrong'}])
            self.assertFalse(output.exists())

    def test_checked_publication_never_overwrites_existing_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'staged.rvt';source.write_bytes(b'candidate')
            output=Path(directory)/'verified.rvt'
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(publish_checked(source,output,[{'candidate_sha256':sha}]),sha)
            self.assertEqual(output.read_bytes(),b'candidate')
            with self.assertRaises(FileExistsError):publish_checked(source,output,[{'candidate_sha256':sha}])
            self.assertEqual(output.read_bytes(),b'candidate')

if __name__=='__main__':unittest.main()
