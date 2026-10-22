import struct
import unittest
from dataclasses import replace
from element_table import Table,decode,encode,validate


def sample(width,owners=(None,1,2)):
    stride=28 if width==4 else 40;id_at=4 if width==4 else 20;owner_at=24 if width==4 else 28
    rows=[]
    for ident,owner in enumerate(owners,1):
        r=bytearray(stride);r[:width]=ident.to_bytes(width,'little');r[id_at:id_at+width]=ident.to_bytes(width,'little')
        r[owner_at:owner_at+width]=((1<<(width*8))-1 if owner is None else owner).to_bytes(width,'little')
        rows.append(bytes(r))
    tail=bytearray(19 if width==4 else 24);tail[4:8]=b'\xff'*4;struct.pack_into('<H',tail,8,2305)
    at=11 if width==4 else 12;tail[at:at+width]=(10).to_bytes(width,'little')
    return Table(1411,width,tuple(rows),bytes(tail))

class ElementTableTests(unittest.TestCase):
    def test_roundtrip_and_owner_depth(self):
        for width in (4,8):
            t=sample(width);self.assertEqual(decode(encode(t),width),t)
            self.assertEqual(validate(t)['maximum_owner_chain_nodes'],3)

    def test_missing_owners_cycles_sorting_ceiling_and_count(self):
        for width in (4,8):
            for owners in [(None,99,2),(3,1,2),(1,None,2)]:
                with self.assertRaises(ValueError):validate(sample(width,owners))
            t=sample(width)
            with self.assertRaises(ValueError):validate(replace(t,rows=t.rows[::-1]))
            tail=bytearray(t.trailer);at=11 if width==4 else 12;tail[at:at+width]=bytes(width)
            with self.assertRaises(ValueError):validate(replace(t,trailer=bytes(tail)))
            raw=bytearray(encode(t));struct.pack_into('<I',raw,2,4)
            with self.assertRaises(ValueError):decode(raw,width)
            with self.assertRaises(ValueError):decode(encode(t)+b'\x00',width)

    def test_deep_owner_chain_does_not_recurse(self):
        t=sample(8,tuple([None]+list(range(1,5000))))
        tail=bytearray(t.trailer);tail[12:20]=(5001).to_bytes(8,'little')
        self.assertEqual(validate(replace(t,trailer=bytes(tail)))['maximum_owner_chain_nodes'],5000)

    def test_opaque_fields_and_original_ids_survive(self):
        for width in (4,8):
            t=sample(width)
            row=bytearray(t.rows[0])
            row[:width]=(99).to_bytes(width,'little')
            struct.pack_into('<I',row,8,17)
            row[12:20]=bytes(range(8))
            t=replace(t,rows=(bytes(row),)+t.rows[1:])
            decoded=decode(encode(t),width)
            self.assertEqual(decoded,t)
            self.assertEqual(decoded.episode(decoded.rows[0]),17)
            self.assertEqual(validate(decoded)['primary_current_id_differences'],1)
