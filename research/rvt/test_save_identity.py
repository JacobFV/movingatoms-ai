import copy
import hashlib
import json
from pathlib import Path
import struct
import unittest
import zlib
from save_identity import patch_contents_payload, inflated, REVISION_NAMES, patch_basic_file_info


class ContentsRevisionTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads((Path(__file__).parent/'results/save-identity.json').read_bytes())[2]
        self.raw = bytes.fromhex(self.evidence['contents_inflated_hex'])
        self.header = bytes.fromhex(self.evidence['contents_header_hex'])
        self.logical = self.header+zlib.compress(self.raw, wbits=31)
        self.evidence['contents_logical_sha256'] = hashlib.sha256(self.logical).hexdigest()

    def test_identity_and_known_revision_only(self):
        self.assertEqual(patch_contents_payload(self.logical, self.evidence, {}), self.logical)
        result = patch_contents_payload(self.logical, self.evidence, {'history': 285, 'formats': 176})
        raw, suffix = inflated(result, len(self.header))
        expected = bytearray(self.raw); struct.pack_into('<i', expected, 164, 285)
        self.assertEqual(raw, expected)
        self.assertEqual(suffix, b'')
        self.assertEqual(struct.unpack_from('<i', result, len(self.header)-4)[0], 176)
        self.assertEqual(result[:len(self.header)-4], self.header[:-4])

    def test_stale_evidence_and_unknown_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source changed'):
            patch_contents_payload(self.logical+b'x', self.evidence, {})
        with self.assertRaisesRegex(ValueError, 'unknown revision'):
            patch_contents_payload(self.logical, self.evidence, {'unknown': 5})
        for bad in [True, 2**31, -2**31-1]:
            with self.assertRaises(ValueError):
                patch_contents_payload(self.logical, self.evidence, {'history': bad})

    def test_schema_span_disagreement_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['contents_root']['fields']['m_streamRevisions']['m_historyStreamRevision'] += 1
        with self.assertRaisesRegex(ValueError, 'value disagrees'):
            patch_contents_payload(self.logical, evidence, {'history': 285})
        evidence = copy.deepcopy(self.evidence)
        span = next(s for s in evidence['contents_root']['field_spans'] if s['name']=='m_historyStreamRevision')
        evidence['contents_root']['field_spans'].append(span)
        with self.assertRaisesRegex(ValueError, 'ambiguous revision'):
            patch_contents_payload(self.logical, evidence, {'history': 285})


class BasicCounterTests(unittest.TestCase):
    def setUp(self):
        keys = ('Unique Document Increments', "Central model's version number corresponding to the last reload latest")
        self.raw = b'opaque' + ''.join(key+': 85\r\n' for key in keys).encode('utf-16-le') + b'end'
        spans = {}
        for key in keys:
            start = self.raw.index((key+': ').encode('utf-16-le')) + len((key+': ').encode('utf-16-le'))
            spans[key] = {'start': start, 'end': start+4, 'value': '85'}
        self.evidence = {'basic_file_info_sha256': hashlib.sha256(self.raw).hexdigest(),
                         'document_increments': 85, 'basic_file_info_property_spans': spans}

    def test_two_counters_only(self):
        result = patch_basic_file_info(self.raw, self.evidence, 86)
        self.assertEqual(result, self.raw.replace('85'.encode('utf-16-le'), '86'.encode('utf-16-le')))
        self.assertEqual(patch_basic_file_info(self.raw, self.evidence, 85), self.raw)

    def test_invalid_width_stale_hash_and_span(self):
        for value in [100, True, -1, 2**31]:
            with self.assertRaises(ValueError):
                patch_basic_file_info(self.raw, self.evidence, value)
        with self.assertRaisesRegex(ValueError, 'source changed'):
            patch_basic_file_info(self.raw+b'!', self.evidence, 86)
        self.evidence['basic_file_info_property_spans']['Unique Document Increments']['start'] += 2
        with self.assertRaisesRegex(ValueError, 'span disagrees'):
            patch_basic_file_info(self.raw, self.evidence, 86)

    def test_guid_and_counter_pair_changes(self):
        guid = '49409459-71bb-4a7f-9f74-674b7dd20d9d'
        next_guid = '01234567-89ab-4cde-8f01-23456789abcd'
        keys = ('Unique Document GUID', "Central model's episode GUID corresponding to the last reload latest")
        source = self.raw + ''.join(key+': '+guid+'\r\n' for key in keys).encode('utf-16-le')
        evidence = copy.deepcopy(self.evidence)
        evidence['document_guid'] = guid
        evidence['basic_file_info_sha256'] = hashlib.sha256(source).hexdigest()
        for key in keys:
            start = source.index((key+': ').encode('utf-16-le')) + len((key+': ').encode('utf-16-le'))
            evidence['basic_file_info_property_spans'][key] = {'start': start, 'end': start+72, 'value': guid}
        result = patch_basic_file_info(source, evidence, 86, next_guid)
        expected = source.replace('85'.encode('utf-16-le'), '86'.encode('utf-16-le')).replace(guid.encode('utf-16-le'), next_guid.encode('utf-16-le'))
        self.assertEqual(result, expected)
        with self.assertRaisesRegex(ValueError, 'invalid document GUID'):
            patch_basic_file_info(source, evidence, 86, 'no-guid')
