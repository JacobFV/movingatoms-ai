from copy import deepcopy
import math
import json
from pathlib import Path
import unittest
from seed_wall_verify import WIDTH,global_check,vertices,wall_semantics


def ident(i):return {'m_id':{'m_id64':i}}

def globals_fixture():
    objects=[]
    for name,fields in [('StructuralElemSetTracking',{'m_elemIdSet':[]}),('DatumTracking',{'m_elemIdSet':[ident(1916)]}),('ElementTrackingData',{'m_elems':[{'m_categoryId':ident(-2000240),'m_elemIdSet':[ident(1916)]}]}),('LevelPlanViewTracking',{'m_levelIdToPlanViewIds':[]})]:
        objects.append({'class_name':name,'class_tag':len(objects)+1,'token':0,'fields':fields})
    return {'objects':objects,'edges':[]}


class SeedWallVerifyTests(unittest.TestCase):
    def test_oracle_uses_200mm_and_zero_base(self):
        points=vertices({'length_feet':12,'height_feet':9,'translation_xy':[-119.5,-67.75],'yaw_degrees':90})
        self.assertAlmostEqual(max(p[0]for p in points)-min(p[0]for p in points),WIDTH)
        self.assertAlmostEqual(max(p[1]for p in points),12)
        self.assertEqual({p[2]for p in points},{0,9})
        self.assertAlmostEqual(WIDTH*.3048,.2)

    def test_oracle_refuses_nonfinite_input(self):
        for bad in (float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):vertices({'length_feet':bad,'translation_xy':[0,0]})

    def test_global_exact_three_lists_and_reject_unrelated_change(self):
        before=globals_fixture();after=deepcopy(before)
        after['objects'][0]['fields']['m_elemIdSet']=[ident(2747),ident(2748)]
        after['objects'][1]['fields']['m_elemIdSet'].append(ident(2746))
        after['objects'][2]['fields']['m_elems'][0]['m_elemIdSet'].append(ident(2746))
        self.assertEqual(global_check(before,after,[2747,2748],2746)['changed_lists'],3)
        after['objects'][3]['fields']['m_levelIdToPlanViewIds']=[{'invented':2746}]
        with self.assertRaises(ValueError):global_check(before,after,[2747,2748],2746)

    def test_wall_type_field_matches_measured_source_schema(self):
        profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
        fields=profile['graphs']['102']['objects'][0]['fields']
        self.assertIn('m_WallAttributesId',fields)
        self.assertNotIn('m_attrId',fields)
        self.assertEqual(fields['m_WallAttributesId'],ident(17328))

    def test_wall_context_and_top_offset_independent_checks(self):
        fields={k:ident(v)for k,v in {'m_id':2747,'m_WallAttributesId':1947,'m_assocLevelId':1916,'m_upToLevelId':2746,'m_createdPhaseId':4}.items()};fields['m_roomBounding']=False
        graph={'objects':[{'class_name':'SWall','fields':fields},{'class_name':'AnalyticalSpaceBoundingCell','fields':{'m_isSpaceBounding':False}},{'class_name':'ParamValueSetDouble','fields':{'m_paramSet':[{'m_paramId':ident(k),'m_value':v}for k,v in {-1001108:0,-1001109:-6,-1001101:9}.items()]}}]}
        self.assertEqual(wall_semantics(graph,2747,2746,9)['top_offset_feet'],-6)
        graph['objects'][0]['fields']['m_WallAttributesId']=ident(17328)
        with self.assertRaises(ValueError):wall_semantics(graph,2747,2746,9)
        graph['objects'][0]['fields']['m_WallAttributesId']=ident(1947)
        graph['objects'][0]['fields']['m_assocLevelId']=ident(20308)
        with self.assertRaises(ValueError):wall_semantics(graph,2747,2746,9)

if __name__=='__main__':unittest.main()
