import struct
import unittest
from wall_batch_metadata_audit import audit_table, audit_history, registration_check, sha


def row(ident, episode=1):
    return struct.pack('<QIIIQQI', ident, episode, episode, episode, ident, 2**64-1, 0)


def table(rows, last):
    tail = b'\0'*4+b'\xff'*4+struct.pack('<H', 2305)+b'\0\0'+struct.pack('<Q', last)+b'\0'*4
    return struct.pack('<HI', 100, len(rows))+b''.join(rows)+tail


def history(guids):
    return (struct.pack('<HIIIii', 1279, 1, 1, 0, len(guids), 0)+b'\0'*80
            +struct.pack('<II', 0, len(guids))+b''.join(g+b'\x28' for g in guids)+b'\0'*4)


class BatchMetadataAuditTests(unittest.TestCase):
    def test_three_sequential_ids_share_one_episode(self):
        old = table([row(5), row(7)], 9)
        new = table([row(5), row(7)]+[row(i, 2) for i in (10, 11, 12)], 12)
        result = audit_table(old, new, 2)
        self.assertEqual(result['new_ids'], [10, 11, 12])
        self.assertEqual(result['new_row_episode_fields'], [2, 2, 2])
        self.assertTrue(result['all_source_rows_byte_identical'])

    def test_future_episode_or_old_row_change_fails(self):
        old = table([row(5), row(7)], 9)
        for rows in ([row(5), row(7), row(10, 3)], [row(5, 2), row(7), row(10, 2)]):
            with self.assertRaises(ValueError):
                audit_table(old, table(rows, 10), 2)

    def test_exactly_one_new_history_episode(self):
        old = history([b'a'*16, b'b'*16]); new = history([b'c'*16, b'a'*16, b'b'*16])
        result = audit_history(old, new)
        self.assertEqual(result['creation_episode'], 2)
        self.assertEqual(result['new_history_count'], 3)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            audit_history(old, history([b'd'*16, b'c'*16, b'a'*16, b'b'*16]))
        changed = bytearray(new); changed[22] = 1
        with self.assertRaisesRegex(ValueError, 'preexisting History'):
            audit_history(old, bytes(changed))

    def test_repeated_allocator_with_original_history(self):
        # Regression for accidental per-wall episode allocation; no fixture files.
        from new_element import allocate_identity
        from element_table import decode, encode
        from save_history import decode as history_decode
        old = table([row(5), row(7)], 9)
        current = decode(old, 8); original_history = history_decode(history([b'a'*16, b'b'*16]))
        ids = []
        for _ in range(3):
            ident, current = allocate_identity(current, original_history); ids.append(ident)
        self.assertEqual(audit_table(old, encode(current), 2)['new_ids'], ids)
        self.assertEqual(ids, [10, 11, 12])

    def test_registration_is_only_sorted_union_splice(self):
        old_set = struct.pack('<Iqq', 2, 5, 7)
        source = b'prefix'+old_set+b'suffix'
        evidence = {'inflated_sha256': sha(source), 'object': {'class_name': 'StructuralElemSetTracking',
            'field_spans': [{'name': 'm_elemIdSet', 'start': 6, 'end': 26}]}}
        new = b'prefix'+struct.pack('<Iqqqqq', 5, 5, 7, 10, 11, 12)+b'suffix'
        self.assertTrue(registration_check(source, new, [10, 11, 12], evidence)['sorted_unique_union'])
        with self.assertRaisesRegex(ValueError, 'unexpected Global'):
            registration_check(source, new+b'!', [10, 11, 12], evidence)
        with self.assertRaisesRegex(ValueError, 'sorted unique'):
            registration_check(source, new, [10, 10], evidence)
