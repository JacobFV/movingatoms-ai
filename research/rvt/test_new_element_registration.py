from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from new_element_registration import extended_set,id_set_bytes,register,verify_graph

REPORT=json.loads((Path(__file__).parent/'results/new-element-registration.json').read_bytes())

class RegistrationTests(unittest.TestCase):
    def test_id_set_span_and_uniqueness_guards(self):
        data=id_set_bytes([5,7]);span={'start':0,'end':len(data)}
        self.assertEqual(extended_set(data,span,[5,7],6)[2],id_set_bytes([5,6,7]))
        for ids,new in [([5,7],7),([7,5],6),([5,5],6),([5,9],6)]:
            with self.assertRaises(ValueError):extended_set(data,span,ids,new)
        with self.assertRaises(ValueError):extended_set(data,dict(span,end=len(data)+1),[5,7],6)

    def test_three_lists_only_and_source_hash_guard(self):
        evidence=deepcopy(REPORT['source_evidence']);raw=bytearray(REPORT['before_bytes'])
        for change in REPORT['changes']:
            start,end=change['span_before']['start'],change['span_before']['end']
            raw[start:end]=id_set_bytes(change['ids_before'])
        raw=bytes(raw);evidence['inflated_sha256']=hashlib.sha256(raw).hexdigest()
        result,changes=register(raw,evidence,133210)
        self.assertEqual(len(result)-len(raw),24);self.assertEqual(len(changes),3)
        # Undo edits in ascending source order, accounting for bytes already inserted.
        offset=0
        for change in sorted(changes,key=lambda c:c['span_before']['start']):
            start=change['span_before']['start']+offset
            expected=id_set_bytes(change['ids_after'])
            self.assertEqual(result[start:start+len(expected)],expected)
            offset+=8
        with self.assertRaises(ValueError):register(raw+b'x',evidence,133210)
        with self.assertRaises(ValueError):register(raw,evidence,80437)

    def test_semantic_graph_rejects_unrelated_changes(self):
        ident=lambda n:{'m_id':{'m_id64':n}}
        before={'objects':[
            {'class_name':'ElemsSetWithCellsTracking','class_tag':1,'token':1,'start':1,'fields':{'m_elemIdSetMap':[{'first':-100,'second':{'m_idSet':[ident(80437)]}}]}},
            {'class_name':'EStorageTracking','class_tag':2,'token':2,'start':10,'fields':{'m_trackingItems':[{'m_elemIdSet':[ident(80437)]},{'m_elemIdSet':[ident(80437)]}]}}
        ],'edges':[]}
        changes=[{'class_name':'ElemsSetWithCellsTracking','field':'m_elemIdSetMap','item_index':0,'ids_after':[80437,133210]}]
        changes += [{'class_name':'EStorageTracking','field':'m_trackingItems','item_index':i,'ids_after':[80437,133210]} for i in (0,1)]
        after=deepcopy(before);after['objects'][1]['start']+=8
        after['objects'][0]['fields']['m_elemIdSetMap'][0]['second']['m_idSet'].append(ident(133210))
        for i in (0,1):after['objects'][1]['fields']['m_trackingItems'][i]['m_elemIdSet'].append(ident(133210))
        self.assertEqual(len(verify_graph(before,after,changes,133210)),3)
        after['objects'][0]['fields']['m_elemIdSetMap'][0]['first']=123
        with self.assertRaises(ValueError):verify_graph(before,after,changes,133210)

if __name__=='__main__':unittest.main()
