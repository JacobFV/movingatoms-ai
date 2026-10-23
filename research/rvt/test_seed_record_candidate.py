import json,tempfile,unittest
from pathlib import Path
from seed_record_candidate import checked_records,check_registration,make,sha,SOURCE_SHA

class GenericRecordTests(unittest.TestCase):
    def test_records_require_order_and_complete_channels(self):
        good={'element_id':2746,'channels':{c:b'\x01\x00'for c in (101,102,103)}}
        self.assertEqual(checked_records([good],2746)[0]['id'],2746)
        for bad in ({'id':2747,'bodies':good['channels']},{'id':2746,'bodies':{101:b'xx'}},{'id':2746,'bodies':{**good['channels'],102:bytearray(b'xx')}}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):checked_records([bad],2746)
        with self.assertRaises(ValueError):checked_records([good,good],2746)
    def test_explicit_unchanged_global_requires_bound_policy(self):
        raw=b'abc'+bytes(4);e={'source_sha256':SOURCE_SHA,'source_global_sha256':sha(raw),'registered_global_sha256':sha(raw),'method':'explicit no-registration hypothesis','changes':[]}
        self.assertEqual(check_registration(raw,raw,e),e)
        for key in e:
            bad=dict(e);del bad[key]
            with self.assertRaises(ValueError):check_registration(raw,raw,bad)
        altered=b'changed'+bytes(4)
        with self.assertRaises(ValueError):check_registration(raw,altered,e)
        e['registered_global_sha256']=sha(altered)
        with self.assertRaises(ValueError):check_registration(raw,altered,e)
    def test_real_records_metadata_and_no_clobber(self):
        import olefile
        from codec import decode
        from save_candidate import unpack_global
        from partition_segments import decode as decode_partition
        from partition_objects import validate
        from save_increments import decode as decode_increments
        base=Path(__file__).parent;source=base/'local/minimal_seed-Project.rvt';candidate=base/'local/seed-wall-preflight.rvt'
        if not candidate.exists():self.skipTest('licensed seed candidate not generated')
        with olefile.OleFileIO(source)as f:original=unpack_global(decode(f.openstream('Global/Latest').read()))[0]
        with olefile.OleFileIO(candidate)as f:
            registered=unpack_global(decode(f.openstream('Global/Latest').read()))[0]
            channels=validate(decode_partition(decode(f.openstream('Partitions/1').read())).segments[0],8)
        records=[{'element_id':r.element_id,'channels':{c:channels[c][i].body for c in (101,102,103)}}for i,r in enumerate(channels[101][:-1])]
        context=json.loads((base/'results/seed_save_context.json').read_bytes())
        evidence={'source_sha256':SOURCE_SHA,'source_global_sha256':sha(original),'registered_global_sha256':sha(registered),'method':'independently audited preflight tracker bytes','changes':[{'evidence':'seed native verification'}]}
        with tempfile.TemporaryDirectory()as tmp:
            dest=Path(tmp)/'out';args=(source,dest,records,context,registered,evidence)
            kwargs={'episode_guid':'735a012c-2670-505f-86c8-83c54fb9983e','timestamp':1792627200,'acknowledge_hypotheses':True}
            result=make(*args,**kwargs)
            self.assertEqual(result['expected_new_ids'],[2746,2747,2748,2749]);self.assertTrue(result['all_source_rows_preserved'])
            _,increments=decode_increments(unpack_global((dest/'Global-DocumentIncrementTable.bin').read_bytes())[0])
            self.assertEqual(increments['m_increments'][-1]['m_totalElements'],4)
            self.assertEqual(increments['m_increments'],increments['m_localIncrements'])
            before=(dest/'plan.json').read_bytes()
            with self.assertRaises(FileExistsError):make(*args,**kwargs)
            self.assertEqual((dest/'plan.json').read_bytes(),before)
            with self.assertRaises(ValueError):make(source,Path(tmp)/'missing',records,context,registered,evidence,episode_guid=kwargs['episode_guid'],timestamp=kwargs['timestamp'])
            self.assertFalse((Path(tmp)/'missing').exists())

if __name__=='__main__':unittest.main()
