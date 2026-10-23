import unittest,json,struct
from pathlib import Path
from dataclasses import replace
import element_table,save_history,save_increments
from seed_save_context import allocation_plan

class SeedSavePlanTests(unittest.TestCase):
    def setUp(self):
        import olefile
        from codec import decode
        from save_candidate import unpack_global
        source=Path(__file__).parent/'local/minimal_seed-Project.rvt'
        if not source.exists():self.skipTest('licensed seed not fetched')
        with olefile.OleFileIO(source) as f:
            def raw(name):return unpack_global(decode(f.openstream('Global/'+name).read()))[0]
            self.table=element_table.decode(raw('ElemTable'),8)
            self.history=save_history.decode(raw('History'))
            _,self.fields=save_increments.decode(raw('DocumentIncrementTable'))
    def plan(self,count=3,history=None,timestamp=None):
        return allocation_plan(self.table,history or self.history,self.fields,count,timestamp or self.fields['m_increments'][-1]['m_atimeStamp']['m_lsb']+60,'67876160-3898-55f4-a25a-4b9dfc3e4ab3')
    def test_allocator_ceiling_not_max_live(self):
        result=self.plan();self.assertEqual(result['allocated'],[2746,2747,2748]);self.assertEqual(result['new_episode_id'],1)
        self.assertEqual(result['new_major_version'],2)
        for key in ('m_increments','m_localIncrements'):
            rows=result['increment_fields'][key];self.assertEqual(rows[:-1],self.fields[key]);self.assertEqual(rows[-1]['m_totalElements'],3);self.assertEqual(rows[-1]['m_incrementVersions'],[{'m_causedByIncrementNumber':-1,'m_totalElements':3}])
    def test_invalid_count(self):
        for count in (0,101,True,1.2):
            with self.subTest(count=count),self.assertRaises(ValueError):self.plan(count)
    def test_bad_episode_state(self):
        with self.assertRaises(ValueError):self.plan(history=replace(self.history,next_sequence=2))
    def test_nonincreasing_timestamp(self):
        with self.assertRaises(ValueError):self.plan(timestamp=self.fields['m_increments'][-1]['m_atimeStamp']['m_lsb'])
    def test_seed_registration_source_guard_and_exact_splices(self):
        import olefile
        from codec import decode
        from save_candidate import unpack_global
        from seed_save_context import register_seed
        base=Path(__file__).parent
        evidence=json.loads((base/'results/seed_save_context.json').read_bytes())['registration_evidence']
        with olefile.OleFileIO(base/'local/minimal_seed-Project.rvt')as f:raw=unpack_global(decode(f.openstream('Global/Latest').read()))[0]
        changed,rows=register_seed(raw,evidence,[2747,2748],[2746])
        self.assertEqual(len(changed)-len(raw),32);self.assertEqual(len(rows),3)
        reversed_bytes=changed;growth=0
        patches=sorted(rows,key=lambda r:r['span']['start'])
        for row in reversed(patches):
            prior=sum(8*(len(r['after'])-len(r['before']))for r in patches if r['span']['start']<row['span']['start'])
            start=row['span']['start']+prior
            from new_element_registration import id_set_bytes
            old=id_set_bytes(row['before']);new=id_set_bytes(row['after'])
            self.assertEqual(reversed_bytes[start:start+len(new)],new)
            reversed_bytes=reversed_bytes[:start]+old+reversed_bytes[start+len(new):]
        self.assertEqual(reversed_bytes,raw)
        with self.assertRaises(ValueError):register_seed(raw+b'x',evidence,[2747],[2746])
        with self.assertRaises(ValueError):register_seed(raw,evidence,[2746],[2746])
    def test_seed_project_timestamp_guard(self):
        import olefile
        from seed_save_context import patch_seed_timestamp
        from project_information_codec import parse
        with olefile.OleFileIO(Path(__file__).parent/'local/minimal_seed-Project.rvt')as f:raw=f.openstream('ProjectInformation').read()
        oldts=self.fields['m_increments'][-1]['m_atimeStamp']['m_lsb']
        self.assertEqual(patch_seed_timestamp(raw,oldts,oldts)[0],raw)
        new,evidence=patch_seed_timestamp(raw,oldts,oldts+60)
        self.assertEqual(evidence['source_timestamp_offset_seconds'],10800)
        before,stamp,*_=parse(raw);after,newstamp,*_=parse(new)
        self.assertEqual(before.replace(stamp.encode(),newstamp.encode()),after)
        with self.assertRaises(ValueError):patch_seed_timestamp(raw,oldts+1,oldts+60)

    def test_seed_contents_suffix_and_revision_only_change(self):
        import olefile,hashlib,zlib
        from codec import decode
        from seed_save_context import patch_seed_contents
        from save_identity import inflated,revision_spans,patch_contents_payload
        base=Path(__file__).parent;evidence=json.loads((base/'results/seed_save_context.json').read_bytes())
        with olefile.OleFileIO(base/'local/minimal_seed-Project.rvt')as f:logical=decode(f.openstream('Contents').read())
        with self.assertRaises(ValueError):patch_contents_payload(logical,evidence,{'history':1})
        self.assertEqual(patch_seed_contents(logical,evidence,{}),logical)
        changed=patch_seed_contents(logical,evidence,{'history':1,'formats':2})
        before,tail=inflated(logical,91);after,newtail=inflated(changed,91)
        self.assertEqual(tail,b'\0');self.assertEqual(newtail,tail)
        expected=bytearray(before);struct.pack_into('<i',expected,revision_spans(before,evidence)['history'][0],1)
        self.assertEqual(after,bytes(expected));self.assertEqual(changed[:87],logical[:87]);self.assertEqual(struct.unpack_from('<i',changed,87)[0],2)
        for bad in (logical[:-1],logical[:-1]+b'x',logical+b'\0'):
            with self.subTest(tail=bad[-2:]),self.assertRaises(ValueError):patch_seed_contents(bad,evidence,{'history':1})
        bad_evidence=dict(evidence,contents_gzip_suffix_hex='0000')
        with self.assertRaises(ValueError):patch_seed_contents(logical,bad_evidence,{'history':1})

if __name__=='__main__':unittest.main()
