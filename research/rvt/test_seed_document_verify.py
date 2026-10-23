from copy import deepcopy
import math
import unittest
from seed_document_verify import request_oracle,vertices,global_check,wall_semantics
from test_seed_wall_verify import globals_fixture,ident


def request():
    return {'schema_version':1,'units':'metres','levels':[{'name':'Basement Δ','elevation':-3},{'name':'Level 1','elevation':0},{'name':'Roof 😀','elevation':6}],
            'walls':[{'id':'wall-app-a','base_level':'Basement Δ','top_level':'Roof 😀','start':[1,2],'length':4,'height':3,'yaw_degrees':90}]}


class SeedDocumentVerifyTests(unittest.TestCase):
    def test_independent_si_allocation_and_scaffold_reuse(self):
        result=request_oracle(request())
        self.assertEqual(result['new_level_ids'],[2746,2747]);self.assertEqual(result['new_wall_ids'],[2748])
        self.assertEqual([l['element_id']for l in result['levels']],[2746,1916,2747])
        self.assertEqual(result['walls'][0]['id'],'wall-app-a')
        altered=request();altered['levels'][1]['name']='Ground'
        changed=request_oracle(altered);self.assertEqual(changed['new_level_ids'],[2746,2747,2748]);self.assertEqual(changed['new_wall_ids'],[2749])

    def test_physical_oracle_uses_world_metres_negative_base(self):
        w=request_oracle(request())['walls'][0];p=vertices({**w['request'],'base_elevation_m':w['base_elevation_m']})
        metric=[[c*.3048 for c in v]for v in p]
        self.assertAlmostEqual(min(v[0]for v in metric),.9);self.assertAlmostEqual(max(v[0]for v in metric),1.1)
        self.assertAlmostEqual(min(v[1]for v in metric),2);self.assertAlmostEqual(max(v[1]for v in metric),6)
        self.assertEqual({round(v[2],9)for v in metric},{-3,0})

    def test_rejects_wrong_units_ambiguous_ids_and_invalid_shapes(self):
        cases=[]
        r=request();r['units']='feet';cases.append(r)
        r=request();r['levels'][1]['elevation']=1;cases.append(r)
        r=request();r['levels'][1]['name']='LEVEL 1';cases.append(r)
        r=request();r['levels'][0]['elevation']=True;cases.append(r)
        r=request();r['levels'][0]['elevation']=float('nan');cases.append(r)
        r=request();r['walls'][0]['thickness']=.2032;cases.append(r)
        r=request();r['walls'][0]['kind']='curved';cases.append(r)
        r=request();r['walls'].append(deepcopy(r['walls'][0]));cases.append(r)
        r=request();r['walls'][0]['top_level']='Basement Δ';cases.append(r)
        r=request();r['levels'].append(deepcopy(r['levels'][0]));cases.append(r)
        for r in cases:
            with self.assertRaises(ValueError):request_oracle(r)

    def test_global_multiple_levels_preserves_existing_plan_maps(self):
        before=globals_fixture();after=deepcopy(before)
        after['objects'][0]['fields']['m_elemIdSet']=[ident(2748)]
        after['objects'][1]['fields']['m_elemIdSet']=[ident(1916),ident(2746),ident(2747)]
        after['objects'][2]['fields']['m_elems'][0]['m_elemIdSet']=[ident(1916),ident(2746),ident(2747)]
        self.assertEqual(global_check(before,after,[2748],[2746,2747])['changed_lists'],3)
        after['objects'][1]['fields']['m_elemIdSet'].pop(0)
        with self.assertRaises(ValueError):global_check(before,after,[2748],[2746,2747])

    def test_native_constraints_use_selected_levels_and_metric_top_offset(self):
        w=request_oracle(request())['walls'][0];fields={k:ident(v)for k,v in {'m_id':2748,'m_WallAttributesId':1947,'m_assocLevelId':2746,'m_upToLevelId':2747,'m_createdPhaseId':4}.items()};fields['m_roomBounding']=False
        g={'objects':[{'class_name':'SWall','fields':fields},{'class_name':'AnalyticalSpaceBoundingCell','fields':{'m_isSpaceBounding':False}},{'class_name':'ParamValueSetDouble','fields':{'m_paramSet':[{'m_paramId':ident(k),'m_value':v}for k,v in {-1001108:0,-1001109:-6/.3048,-1001101:3/.3048}.items()]}}]}
        self.assertAlmostEqual(wall_semantics(g,2748,w)['top_offset_feet'],-6/.3048)
        g['objects'][0]['fields']['m_assocLevelId']=ident(1916)
        with self.assertRaises(ValueError):wall_semantics(g,2748,w)

if __name__=='__main__':unittest.main()
