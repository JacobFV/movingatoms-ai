from copy import deepcopy
import json,struct,unittest,zlib
from pathlib import Path
from seed_metadata_audit import streams,audit_streams,inflate_contents
from codec import decode,encode
from save_candidate import repack_global
from save_increments import decode as decode_increments,encode as encode_increments
from wall_batch_metadata_audit import inflate_global

class SeedMetadataAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=Path(__file__).parent
        if not (base/'local/seed-wall-preflight.rvt').exists():raise unittest.SkipTest('licensed seed preflight not generated')
        cls.old=streams(base/'local/minimal_seed-Project.rvt');cls.new=streams(base/'local/seed-wall-preflight.rvt')
        cls.evidence=json.loads((base/'results/seed_save_context.json').read_bytes())
    def check(self,new=None):return audit_streams(self.old,self.new if new is None else new,self.evidence)
    def change_increment(self,callback):
        changed=dict(self.new);name='Global/DocumentIncrementTable';tag,fields=decode_increments(inflate_global(changed[name]));callback(fields)
        changed[name]=encode(repack_global(decode(changed[name]),encode_increments(tag,fields)));return changed
    def test_actual_file_without_plan(self):
        r=self.check();self.assertEqual(r['table']['new_ids'],[2746,2747,2748,2749]);self.assertEqual(r['new_increment_total_elements'],4)
    def test_stale_second_increment_count(self):
        def corrupt(f):f['m_localIncrements'][-1]['m_totalElements']=1
        with self.assertRaisesRegex(ValueError,'arrays disagree'):self.check(self.change_increment(corrupt))
    def test_both_counts_cannot_lie_together(self):
        def corrupt(f):
            for k in ('m_increments','m_localIncrements'):
                f[k][-1]['m_totalElements']=3;f[k][-1]['m_incrementVersions'][0]['m_totalElements']=3
        with self.assertRaisesRegex(ValueError,'counts differ'):self.check(self.change_increment(corrupt))
    def test_old_increment_cannot_be_rewritten(self):
        def corrupt(f):
            for k in ('m_increments','m_localIncrements'):f[k][0]['m_comment']='changed'
        with self.assertRaisesRegex(ValueError,'old increment rows'):self.check(self.change_increment(corrupt))
    def test_stale_contents_or_removed_zero_suffix(self):
        changed=dict(self.new);changed['Contents']=self.old['Contents']
        with self.assertRaises(ValueError):self.check(changed)
        changed['Contents']=encode(decode(self.new['Contents'])[:-1])
        with self.assertRaisesRegex(ValueError,'suffix'):self.check(changed)
    def test_preserved_stream_and_missing_partition(self):
        changed=dict(self.new);changed['Global/PartitionTable']=b'corrupted'
        with self.assertRaisesRegex(ValueError,'changed source streams'):self.check(changed)
        changed=dict(self.new);changed.pop('Partitions/1')
        with self.assertRaisesRegex(ValueError,'inventory'):self.check(changed)
    def test_stale_xml_timestamp(self):
        changed=dict(self.new);changed['ProjectInformation']=self.old['ProjectInformation']
        with self.assertRaises(ValueError):self.check(changed)
    def test_wrong_contents_revision_with_valid_gzip_and_parity(self):
        changed=dict(self.new);logical=decode(changed['Contents']);body=bytearray(inflate_contents(logical))
        span=next(x for x in self.evidence['contents_root']['field_spans']if x['name']=='m_historyStreamRevision')
        struct.pack_into('<i',body,span['start'],55)
        changed['Contents']=encode(logical[:91]+zlib.compress(bytes(body),wbits=31)+b'\0')
        with self.assertRaisesRegex(ValueError,'Contents revision'):self.check(changed)

    def test_valid_xml_wrong_increment_time(self):
        from seed_save_context import patch_seed_timestamp
        _,fields=decode_increments(inflate_global(self.new['Global/DocumentIncrementTable']))
        _,original=decode_increments(inflate_global(self.old['Global/DocumentIncrementTable']))
        changed=dict(self.new)
        changed['ProjectInformation']=patch_seed_timestamp(self.old['ProjectInformation'],original['m_increments'][-1]['m_atimeStamp']['m_lsb'],fields['m_increments'][-1]['m_atimeStamp']['m_lsb']+60)[0]
        with self.assertRaisesRegex(ValueError,'XML offset'):self.check(changed)
    def test_all_basic_identity_copies_consistently_wrong(self):
        from basic_file_info_codec import decode as parse,encode as write
        changed=dict(self.new);changed['BasicFileInfo']=write(parse(changed['BasicFileInfo']),document_guid='22fdf086-3222-4e0e-bcbb-587627f2577b')
        with self.assertRaisesRegex(ValueError,'BasicFileInfo identity'):self.check(changed)

if __name__=='__main__':unittest.main()
