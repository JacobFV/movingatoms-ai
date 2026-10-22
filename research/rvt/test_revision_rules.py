import unittest
from revision_rules import analyze
from save_increments import REVISIONS


def row(ordinal, offset=0, increment_delta=0):
    r = {f'm_{n}StreamRevision': ordinal+offset for n in REVISIONS}
    r.update(m_majorVersion=ordinal+1, m_totalEpisodes=ordinal+1, m_greatest={'m_id': ordinal})
    r['m_incrementTableStreamRevision'] += increment_delta
    return r


class RevisionRulesTests(unittest.TestCase):
    def test_offsets_are_not_ordinal_revisions(self):
        result = analyze([row(i, 200, 1) for i in range(3)], 3)
        self.assertEqual(result['global_minus_ordinal_values'], [200])
        self.assertEqual(result['fields']['incrementTable']['offsets_from_global'], [1])
        for name in ['global_equals_ordinal', 'increment_table_equals_global']:
            self.assertEqual(result['relationships'][name]['counterexample_ordinals'], [0, 1, 2])
        self.assertTrue(result['relationships']['history_equals_global']['holds_in_this_file'])

    def test_counterexamples_are_reported_not_hidden(self):
        rows = [row(i) for i in range(3)]
        rows[2]['m_historyStreamRevision'] = -1
        rows[1]['m_totalEpisodes'] = 9
        result = analyze(rows, 3)
        self.assertEqual(result['fields']['history']['decreasing_at_ordinals'], [2])
        self.assertEqual(result['relationships']['episode_count_within_current_history']['counterexample_ordinals'], [1])
        self.assertEqual(result['relationships']['history_equals_global']['counterexample_ordinals'], [2])
        self.assertTrue(result['latest_total_episodes_equals_history_count'])

    def test_empty_sequence_fails(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            analyze([], 0)
