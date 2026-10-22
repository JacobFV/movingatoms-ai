import copy
import unittest
from wall_candidate_verify import projection_check


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        wall={'type_guid':'20826','kind':'BuildingElement','ifc_type':'IfcWall',
              'location_feet':[1.0,2.0,0.0],'rotation_radians':0.0,
              'extrusion':{'width_feet':9.5,'depth_feet':2/3,'height_feet':15.0}}
        before={'entities':[wall],'layers':{'20826':['layer']},'native_ids':{'20826':'old'}}
        after=copy.deepcopy(before);new=copy.deepcopy(wall);new['type_guid']='133210';new['location_feet']=[31.0,22.0,0.0]
        after['entities'].append(new);after['layers']['133210']=['layer'];after['native_ids']['133210']='new'
        return before,after
    def test_controlled_projection(self):
        a,b=self.fixture();r=projection_check(a,b);self.assertEqual((r['source_wall_count'],r['candidate_wall_count']),(1,2))
    def test_wrong_displacement_or_dimensions_rejected(self):
        for key,value in [('location_feet',[1.,2.,0.]),('extrusion',{'height_feet':16.})]:
            a,b=self.fixture();b['entities'][-1][key]=value
            with self.assertRaises(ValueError):projection_check(a,b)
    def test_existing_geometry_and_identity_preserved(self):
        a,b=self.fixture();b['entities'][0]['rotation_radians']=1.0
        with self.assertRaises(ValueError):projection_check(a,b)
        a,b=self.fixture();b['native_ids']['20826']='changed'
        with self.assertRaises(ValueError):projection_check(a,b)

if __name__=='__main__':unittest.main()
