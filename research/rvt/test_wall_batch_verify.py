import unittest
import math
from wall_batch_verify import validate_specs,expected_bounds,near,DEFAULT_SPECS,expected_vertices,vertex_set_matches,projection_frame,serialized_oracle,verify_height_constraints

class BatchVerificationTests(unittest.TestCase):
    def test_distinct_lengths_and_positions(self):
        validate_specs(DEFAULT_SPECS)
        self.assertEqual([expected_bounds(s)[1][0]-expected_bounds(s)[0][0]for s in DEFAULT_SPECS],[6,12,18])
    def test_quarter_turn_exchanges_world_extents(self):
        spec={**DEFAULT_SPECS[1],'yaw_degrees':90.};lo,hi=expected_bounds(spec)
        self.assertAlmostEqual(hi[0]-lo[0],2/3);self.assertAlmostEqual(hi[1]-lo[1],12.)
        self.assertTrue(vertex_set_matches(list(reversed(expected_vertices(spec))),expected_vertices(spec),1e-9))
    def test_rotated_vertex_set_rejects_axis_aligned_box(self):
        spec={**DEFAULT_SPECS[0],'yaw_degrees':45.}
        self.assertFalse(vertex_set_matches(expected_vertices(DEFAULT_SPECS[0]),expected_vertices(spec),1e-7))
        self.assertFalse(vertex_set_matches(expected_vertices(spec)[:-1]+[expected_vertices(spec)[0]],expected_vertices(spec),1e-7))
    def test_nonfinite_yaw_rejected(self):
        with self.assertRaises(ValueError):expected_vertices({**DEFAULT_SPECS[0],'yaw_degrees':float('inf')})
    def test_quarter_turn_projection_equivalence(self):
        spec={**DEFAULT_SPECS[1],'yaw_degrees':90.,'translation_xy':[430,20]}
        wall={'location_feet':[549.5,93.75,76.],'rotation_radians':None,'extrusion':{'width_feet':2/3,'depth_feet':12.,'height_feet':15.}}
        self.assertEqual(projection_frame(spec,wall)['quarter_turns'],-1)
        wall['rotation_radians']=math.pi/2
        with self.assertRaises(ValueError):projection_frame(spec,wall)
        wall['rotation_radians']=None;wall['location_feet'][0]+=1
        with self.assertRaises(ValueError):projection_frame(spec,wall)
    def test_wrong_yaw_rejected(self):
        spec={**DEFAULT_SPECS[0],'yaw_degrees':45.};bounds=expected_bounds(spec)
        wall={'location_feet':[(bounds[0][i]+bounds[1][i])/2 for i in range(2)]+[76.],
              'rotation_radians':-math.pi/4,'extrusion':{'width_feet':6.,'depth_feet':2/3,'height_feet':15.}}
        with self.assertRaises(ValueError):projection_frame(spec,wall)
    def test_serialization_precision_is_explicitly_bounded(self):
        spec={**DEFAULT_SPECS[2],'yaw_degrees':-30.};bounds=expected_bounds(spec)
        wall={'location_feet':[(bounds[0][i]+bounds[1][i])/2 for i in range(2)]+[76.],
              'rotation_radians':-math.pi/6,'extrusion':{'width_feet':18.,'depth_feet':2/3,'height_feet':15.}}
        oracle=serialized_oracle(spec,projection_frame(spec,wall));ideal=[[x*.3048 for x in p]for p in expected_vertices(spec)]
        deviation=max(min(math.dist(p,q)for q in ideal)for p in oracle['vertices_metres'])
        self.assertGreater(deviation,1e-8);self.assertLess(deviation,oracle['ideal_vertex_deviation_bound_metres'])
        self.assertEqual(oracle['decimal_places'],6)
    def test_height_oracle_and_wrong_projection_rejected(self):
        spec={**DEFAULT_SPECS[0],'height_feet':10.}
        low,high=expected_bounds(spec)
        self.assertEqual([low[2],high[2]],[76,86])
        wall={'location_feet':[522.5,67.75,76.],'rotation_radians':0.,'extrusion':{'width_feet':6.,'depth_feet':2/3,'height_feet':10.}}
        self.assertEqual(projection_frame(spec,wall)['dimensions_feet'],[6,2/3,10])
        wall['extrusion']['height_feet']=15
        with self.assertRaises(ValueError):projection_frame(spec,wall)
        for height in (True,float('nan'),float('inf'),0):
            with self.assertRaises(ValueError):expected_vertices(dict(spec,height_feet=height))

    def test_native_height_scalar_tampering_rejected(self):
        import json
        from copy import deepcopy
        from pathlib import Path
        from wall_height import height_profile
        profile=json.loads((Path(__file__).parent/'results/wall-element-profile.json').read_bytes())
        graph=height_profile(profile,10)[0]['graphs']['102']
        self.assertTrue(verify_height_constraints(graph,{'height_feet':10})['level_offset_equation_matches_requested_height'])
        for pid in (-1001109,-1001101,-1001105,-1001108):
            broken=deepcopy(graph)
            params=next(o['fields']['m_paramSet']for o in broken['objects']if o['class_name']=='ParamValueSetDouble')
            next(v for v in params if v['m_paramId']['m_id']['m_id64']==pid)['m_value']+=1
            with self.assertRaises(ValueError):verify_height_constraints(broken,{'height_feet':10})
        graph['objects'][0]['fields']['m_upToLevelId']['m_id']['m_id64']=-1
        with self.assertRaises(ValueError):verify_height_constraints(graph,{'height_feet':10})

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):validate_specs([DEFAULT_SPECS[0],DEFAULT_SPECS[0]])
    def test_nonfinite_bounds_rejected(self):
        with self.assertRaises(ValueError):expected_bounds({'length_feet':float('nan'),'translation_xy':[400,0]})
        self.assertFalse(near([float('nan')],[1]))

if __name__=='__main__':unittest.main()
