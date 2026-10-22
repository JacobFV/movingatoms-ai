import unittest
from copy import deepcopy
from pathlib import Path
from save_candidate import append_increment, make, repack_global, unpack_global, advance_regular_ancillary_revisions
from save_increments import REVISIONS
import gzip

class SaveCandidateTests(unittest.TestCase):
    def fields(self):
        row = {'m_greatest': {'m_id': 702}, 'm_majorVersion': 85,
               'm_atimeStamp': {'m_msb': 0, 'm_lsb': 100},
               'm_totalElements': 3, 'm_totalEpisodes': 703,
               'm_incrementVersions': [{'m_causedByIncrementNumber': -1, 'm_totalElements': 3}],
               'm_overwrite': False, 'm_comment': '', 'm_userName': 'fixture'}
        row.update((f'm_{name}StreamRevision', 200) for name in REVISIONS)
        row['m_incrementTableStreamRevision'] = 201
        return {'m_increments': [row], 'm_localIncrements': [deepcopy(row)], 'm_permutation': []}

    def test_revision_offsets_and_history_retention(self):
        before = self.fields(); original = deepcopy(before)
        after = append_increment(before, 703, 101)
        self.assertEqual(before, original)
        self.assertEqual(after['m_increments'][:-1], before['m_increments'])
        self.assertEqual(after['m_increments'], after['m_localIncrements'])
        row = after['m_increments'][-1]
        self.assertEqual(row['m_globalStreamRevision'], 201)
        self.assertEqual(row['m_incrementTableStreamRevision'], 202)
        self.assertEqual(row['m_contentDocumentsStreamRevision'], 200)
        self.assertEqual(row['m_totalElements'], 1)
        self.assertEqual(row['m_greatest'], {'m_id': 703})

    def test_regular_ancillary_policy_preserves_revision_baselines(self):
        before = self.fields()
        revised = append_increment(before, 703, 101)
        changed = advance_regular_ancillary_revisions(before, revised)
        self.assertEqual(changed['m_increments'][-1]['m_contentDocumentsStreamRevision'], 201)
        self.assertEqual(changed['m_increments'][-1]['m_transmissionDataStreamRevision'], 201)
        self.assertEqual(changed['m_increments'][-1]['m_projectXMLInfoStreamRevision'], 201)
        self.assertEqual(changed['m_increments'][-1]['m_previewStreamRevision'], 200)
        self.assertEqual(changed['m_increments'][-1]['m_formatsStreamRevision'], 200)
        self.assertEqual(revised['m_increments'][-1]['m_contentDocumentsStreamRevision'], 200)
        self.assertEqual(changed['m_increments'], changed['m_localIncrements'])
        with self.assertRaises(ValueError): advance_regular_ancillary_revisions(before, before)

    def test_rejects_unestablished_input_states(self):
        for episode, timestamp in [(702,101), (704,101), (703,100), (703,2**32)]:
            with self.assertRaises(ValueError): append_increment(self.fields(), episode, timestamp)
        fields = self.fields(); fields['m_permutation'] = [0]
        with self.assertRaises(ValueError): append_increment(fields,703,101)
        fields = self.fields(); fields['m_increments'][0]['m_atimeStamp']['m_msb'] = 1
        fields['m_localIncrements'] = deepcopy(fields['m_increments'])
        with self.assertRaises(ValueError): append_increment(fields,703,101)
        fields = self.fields(); fields['m_localIncrements'] = []
        with self.assertRaises(ValueError): append_increment(fields,703,101)
        with self.assertRaisesRegex(ValueError, 'acknowledgment'):
            make(Path('/absent'),Path('/absent-output'))
        with self.assertRaisesRegex(ValueError, 'both BasicFileInfo'):
            make(Path('/absent'),Path('/absent-output'), acknowledge_hypotheses=True, synchronize_binary_identity=True)

    def test_global_prefix_suffix_survive_resizing(self):
        old = bytes(range(8))+gzip.compress(b'old',mtime=0)+b'\0\x99'
        changed = repack_global(old,b'larger new data')
        self.assertEqual(changed[:8],old[:8])
        self.assertEqual(unpack_global(changed),(b'larger new data',b'\0\x99'))
        with self.assertRaises(ValueError): unpack_global(old[:12])

if __name__ == '__main__': unittest.main()
