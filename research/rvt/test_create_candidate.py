import unittest
from pathlib import Path
from create_candidate import make

class CreateCandidateTests(unittest.TestCase):
    def test_explicit_hypotheses_required_before_files_are_read(self):
        with self.assertRaisesRegex(ValueError,'acknowledgment'):
            make(Path('/absent'),Path('/absent-output'),{},[])

    def test_wrong_fixture_rejected_before_destination_creation(self):
        import tempfile
        with tempfile.TemporaryDirectory()as tmp:
            source=Path(tmp)/'wrong.rvt';source.write_bytes(b'not a fixture')
            dest=Path(tmp)/'candidate'
            with self.assertRaisesRegex(ValueError,'pinned core2024'):
                make(source,dest,{},[],acknowledge_hypotheses=True)
            self.assertFalse(dest.exists())

if __name__=='__main__':unittest.main()
