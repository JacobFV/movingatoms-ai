from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from new_element_registration import id_set_bytes
from wall_element_registration import register,verify_graph

REPORT=json.loads((Path(__file__).parent/'results/wall-element-registration.json').read_bytes())

class WallRegistrationTests(unittest.TestCase):
    def test_single_id_set_append_is_guarded(self):
        evidence=deepcopy(REPORT);span=evidence['object']['field_spans'][0]
        values=[v['m_id']['m_id64'] for v in evidence['object']['fields']['m_elemIdSet']]
        data=b'\0'*span['start']+id_set_bytes(values)+b'unchanged-suffix'
        evidence['inflated_sha256']=hashlib.sha256(data).hexdigest()
        changed,change=register(data,evidence,133210)
        self.assertEqual(len(changed),len(data)+8)
        self.assertEqual(changed[:span['start']],data[:span['start']])
        self.assertTrue(changed.endswith(b'unchanged-suffix'))
        self.assertEqual(change['ids_after'],values+[133210])
        with self.assertRaises(ValueError):register(data,evidence,20826)
        with self.assertRaises(ValueError):register(data+b'x',evidence,133210)
        evidence['object']['field_spans'][0]['end']-=1
        with self.assertRaises(ValueError):register(data,evidence,133210)

    def test_unrelated_global_graph_change_rejected(self):
        before={'objects':[{'class_name':'StructuralElemSetTracking','class_tag':1,'token':0,'fields':{'m_elemIdSet':[{'m_id':{'m_id64':20826}}],'m_idMRU':-1}}],'edges':[]}
        after=deepcopy(before);after['objects'][0]['fields']['m_elemIdSet'].append({'m_id':{'m_id64':133210}})
        self.assertTrue(verify_graph(before,after,{'ids_after':[20826,133210]}))
        after['objects'][0]['fields']['m_idMRU']=133210
        with self.assertRaises(ValueError):verify_graph(before,after,{'ids_after':[20826,133210]})

if __name__=='__main__':unittest.main()
