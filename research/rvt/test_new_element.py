import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import unittest
import uuid
from element_table import Table, decode, encode
from new_element import data_storage, allocate_identity, Encoder
from save_history import History, prepend_episode

PROFILE=json.loads((Path(__file__).parent/'results/new-element-profile.json').read_bytes())

class NewElementTests(unittest.TestCase):
    def test_measured_source_bodies_reconstruct_exactly(self):
        bodies=data_storage(PROFILE['declarations'],PROFILE['catalog'],80437,'','d5ec174e-6367-4b6c-acc6-aa3b9894332b')
        evidence=json.loads((Path(__file__).parent/'results/new-element.json').read_bytes())
        for seq,body in bodies.items():
            self.assertEqual(hashlib.sha256(body).hexdigest(),evidence['source_channel_reconstruction'][str(seq)]['sha256'])
        self.assertEqual(hashlib.sha256(bodies[102]).hexdigest(),'f027e7b414dcebc337dbdc23c26ddc34cdafb466017cc5c4aea46bcfde212479')

    def test_generated_identity_and_unicode_are_independently_decoded(self):
        evidence=json.loads((Path(__file__).parent/'results/new-element.json').read_bytes())
        bodies=data_storage(PROFILE['declarations'],PROFILE['catalog'],evidence['generated_id'],
                            evidence['generated_name'],evidence['generated_storage_guid'])
        for seq,body in bodies.items():
            self.assertEqual(hashlib.sha256(body).hexdigest(),evidence['channels'][str(seq)]['sha256'])
        root=evidence['decoded_graphs']['102']['objects'][0]['fields']
        self.assertEqual(root['m_name'],'Clean-room DataStorage Δ')
        for channel in evidence['channels'].values():
            self.assertTrue(all(r['id'] in (-1,evidence['generated_id']) for r in channel['element_references']))

    def test_reject_missing_or_changed_schema(self):
        catalog=copy.deepcopy(PROFILE['catalog']);catalog['schemas'].pop(next(iter(catalog['schemas'])))
        with self.assertRaises(ValueError):data_storage(PROFILE['declarations'],catalog,100,'x',uuid.uuid4())
        declarations=copy.deepcopy(PROFILE['declarations'])
        next(c for c in declarations if c['name']=='DataStorage')['fields'][0]['name']='unknown_field'
        with self.assertRaises(ValueError):data_storage(declarations,PROFILE['catalog'],100,'x',uuid.uuid4())
        declarations=copy.deepcopy(PROFILE['declarations'])
        next(c for c in declarations if c['name']=='DataStorage')['fields'][0]['uninterpreted_flags']=1
        with self.assertRaises(ValueError):data_storage(declarations,PROFILE['catalog'],100,'x',uuid.uuid4())

    def test_ambiguous_or_cyclic_schema_rejected(self):
        base=PROFILE['declarations']
        variants=[]
        variants.append(base+[base[0]])
        variant=copy.deepcopy(base);variant[1]['name']=variant[0]['name'];variants.append(variant)
        variant=copy.deepcopy(base);variant[0]['parent_reference']['tag']=65535;variants.append(variant)
        variant=copy.deepcopy(base);variant[0]['parent_reference']['tag']=variant[0]['tag'];variants.append(variant)
        variant=copy.deepcopy(base)
        cls=next(c for c in variant if c['name']=='DataStorage')
        cls['fields'][0]['name']='m_id';variants.append(variant)
        variant=copy.deepcopy(base)
        cls=next(c for c in variant if c['name']=='ElementId')
        cls['fields'][0]['references'][0]['tag']=65535;variants.append(variant)
        for declarations in variants:
            with self.subTest(declarations=variants.index(declarations)):
                with self.assertRaises(ValueError):Encoder(declarations)

    def test_invalid_identifiers_and_strings(self):
        for ident in (-1,0,True,2**63-1):
            with self.assertRaises(ValueError):data_storage(PROFILE['declarations'],PROFILE['catalog'],ident,'x',uuid.uuid4())
        with self.assertRaises(ValueError):data_storage(PROFILE['declarations'],PROFILE['catalog'],100,'x\0y',uuid.uuid4())
        with self.assertRaises(ValueError):data_storage(PROFILE['declarations'],PROFILE['catalog'],100,'x',uuid.UUID(int=0))

    def test_allocator_preserves_existing_and_tracks_new_episode(self):
        row=struct.pack('<QIIIQQI',12,0,0,0,12,2**64-1,0)
        trailer=b'\0'*4+b'\xff'*4+struct.pack('<HHQI',2305,0,20,0)
        table=Table(1,8,(row,),trailer)
        episode=uuid.UUID('0b230fed-999c-43b5-9921-30c853bc0022')
        history=History(1279,0,0,1,0,(bytes(16),)*5,(),(episode.bytes_le+b'\x28',))
        ident,changed=allocate_identity(table,history)
        self.assertEqual(ident,21);self.assertEqual(changed.rows[:-1],table.rows)
        self.assertEqual(changed.last_id,21);self.assertEqual(decode(encode(changed),8),changed)
        self.assertEqual(struct.unpack('<QIIIQQI',changed.rows[-1]),(21,1,1,1,21,2**64-1,0))
        fresh=prepend_episode(history,uuid.UUID('091dce4a-96c2-4443-a171-011237536532').bytes_le)
        self.assertEqual(fresh.episodes[-1],history.episodes[-1])
        with self.assertRaises(ValueError):allocate_identity(table,replace(history,next_sequence=2))

if __name__=='__main__':unittest.main()
