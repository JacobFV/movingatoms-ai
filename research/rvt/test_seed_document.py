import copy
import json
from pathlib import Path
import unittest
from seed_document_request import validate
from seed_document_context import remap
from wall_thickness import encode_wall


def request():
    return {'schema_version':1,'units':'metres','levels':[{'name':'Basement Δ','elevation':-3},{'name':'Ground','elevation':0},{'name':'Roof','elevation':4.2}],
        'walls':[{'id':'west','base_level':'Basement Δ','top_level':'Ground','start':[-5,2],'length':4,'height':2.7,'yaw_degrees':37}]}

class SeedDocumentTests(unittest.TestCase):
    def test_multiple_named_levels_negative_elevation_and_custom_world_start(self):
        checked=validate(request())
        self.assertEqual(checked['levels'][0]['elevation'],-3)
        self.assertEqual(checked['walls'][0]['start'],[-5,2])
        self.assertEqual(checked['walls'][0]['thickness'],0.2)
        self.assertTrue(all(not level['reuse_seed']for level in checked['levels']))

    def test_seed_scaffold_reuse_is_explicit_and_duplicate_names_rejected(self):
        r=request();r['levels'][1]['name']='Level 1';r['walls'][0]['top_level']='Level 1'
        self.assertTrue(validate(r)['levels'][1]['reuse_seed'])
        for name,elevation in [('Level 1',1),('level 1',0),('LEVEL 1',0)]:
            bad=copy.deepcopy(r);bad['levels'][1].update(name=name,elevation=elevation)
            with self.assertRaises(ValueError):validate(bad)
        bad=request();bad['levels'].append({'name':'ground','elevation':10})
        with self.assertRaisesRegex(ValueError,'unique'):validate(bad)

    def test_unsupported_wall_kinds_thickness_fields_and_invalid_geometry(self):
        for field,value in [('kind','curved'),('thickness',0.3),('height',float('nan')),('length',True),('start',[0,float('inf')]),('unexpected',1)]:
            r=request();r['walls'][0][field]=value
            with self.assertRaises(ValueError):validate(r)
        for value in [True,2]:
            r=request();r['schema_version']=value
            with self.assertRaises(ValueError):validate(r)
        r=request();r['walls'][0]['top_level']='missing'
        with self.assertRaises(ValueError):validate(r)

    def test_level_names_and_capacity_are_guarded(self):
        for name in ['', ' Ground','Ground\0','x'*129,'\ud800']:
            r=request();r['levels'][0]['name']=name
            with self.assertRaises(ValueError):validate(r)
        r=request();r['walls']=[{**r['walls'][0],'id':str(i)}for i in range(98)]
        with self.assertRaisesRegex(ValueError,'100 new'):validate(r)

    def test_typed_arbitrary_base_and_seed_top_rebinding(self):
        profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
        _,graphs,_=encode_wall(profile,2750,width_feet=0.2/0.3048,height_feet=8,length_feet=10,
            translation_xy=[-119.5,-67.75],yaw_degrees=25,context=profile['external_references'],
            room_bounding=False,acknowledge_bounding_hypothesis=True,acknowledge_pending_type_remap=True)
        mapping={3:4,87:91,113:119,119:125,681:796,17328:1947,20308:2746,20307:1916}
        result,audit=remap(graphs,profile['declarations'],mapping,new_id=2750,base_level_id=2746,
            base_elevation_feet=-10,top_elevation_feet=0,type_width_feet=0.2/0.3048)
        root=result['102']['objects'][0]['fields']
        self.assertEqual(root['m_assocLevelId']['m_id']['m_id64'],2746)
        self.assertEqual(root['m_upToLevelId']['m_id']['m_id64'],1916)
        self.assertAlmostEqual(result['103']['objects'][0]['fields']['m_bBox'][0][2],-10)
        self.assertAlmostEqual(result['103']['objects'][0]['fields']['m_bBox'][1][2],-2)
        self.assertEqual(audit['top_offset_parameter']['after'],-2)
        from new_element_experiment import references
        self.assertNotIn(2147483647,[r['id']for g in result.values()for r in references([o['fields']for o in g['objects']])])

if __name__=='__main__':unittest.main()
