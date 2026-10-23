"""Corruption controls from an archived independent saved-candidate decode.

The archive contains actual public-reader graphs/scene and table identities,
not reconstructed authoring output. Candidate SHA-256:
8f5f1269cffabff5d5354459b053fc51519c9246dcf858d8a29e319c00c896fe
Reader: b6086d41b9758fd9b92f42f0a47b8345b9c58056
Only the auditor is imported; no model generator is used by these tests.
"""
import base64
from copy import deepcopy
import gzip
import hashlib
import json
import unittest
from seed_model_verify import request_oracle,verify_element,verify_level


class SeedModelCorruptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=gzip.decompress(base64.b64decode(_ARCHIVE))
        if hashlib.sha256(raw).hexdigest()!=_ARCHIVE_SHA256:
            raise AssertionError('archived independent evidence hash differs')
        fixture=json.loads(raw)
        cls.fixture=fixture
        cls.oracle=request_oracle(fixture['request'])
        cls.element=cls.oracle['elements'][0]
        cls.level=cls.oracle['levels'][0]
        cls.context=fixture['context']
        cls.all_ids=set(fixture['all_native_ids'])
        cls.element_actual=next(a for a in fixture['evidence']['records_and_scenes'] if 'scene' in a)
        cls.level_actual=next(a for a in fixture['evidence']['records_and_scenes'] if 'scene' not in a)
        cls.source_graphs={r['channel']:r['graph'] for r in fixture['source_level']['records']}

    def verify(self,actual):
        return verify_element(actual,self.element,self.context,self.all_ids)

    def reject(self,mutate,diagnostic):
        actual=deepcopy(self.element_actual)
        mutate(actual)
        with self.assertRaisesRegex(ValueError,diagnostic):
            self.verify(actual)

    @staticmethod
    def objects(actual,channel):
        return next(r for r in actual['records'] if r['channel']==channel)['graph']['objects']

    @staticmethod
    def primitive(actual):
        return actual['scene']['elements'][0]['meshes']['primitives'][0]

    def test_untampered_archived_reader_output_passes(self):
        self.assertEqual(self.fixture['evidence']['candidate_sha256'],self.fixture['provenance']['candidate_sha256'])
        report=self.verify(deepcopy(self.element_actual))
        self.assertEqual(report['triangle_count'],2)
        self.assertEqual(report['rendered_primitive_count'],2)
        self.assertTrue(verify_level(deepcopy(self.level_actual),self.source_graphs,self.level,self.all_ids)['complete_saved_graphs_match'])

    def test_changed_rendered_vertex_rejected(self):
        def change(actual):self.primitive(actual)['vertices'][0][0]+=.25
        self.reject(change,'rendered triangle multiset')

    def test_changed_native_vertex_rejected(self):
        for channel in (102,103):
            with self.subTest(channel=channel):
                def change(actual):
                    topology=next(o for o in self.objects(actual,channel) if o['class_name']=='FacetedTopology0')
                    topology['fields']['m_pointsArr'][0][0]+=.25
                self.reject(change,'native shape/display triangles')

    def test_reversed_face_winding_rejected(self):
        def change(actual):
            triangle=self.primitive(actual)['triangles'][0]
            triangle[0],triangle[1]=triangle[1],triangle[0]
        self.reject(change,'rendered triangle multiset')

    def test_reversed_unit_normal_rejected(self):
        def change(actual):
            primitive=self.primitive(actual)
            primitive['normals']=[[-v for v in n] for n in primitive['normals']]
        self.reject(change,'normal disagrees with oriented face')

    def test_invalid_normal_length_rejected(self):
        def change(actual):self.primitive(actual)['normals'][0]=[0,0,0]
        self.reject(change,'invalid rendered normals')

    def test_missing_rendered_part_rejected(self):
        def change(actual):actual['scene']['elements'][0]['meshes']['primitives'].pop()
        self.reject(change,'rendered triangle multiset|material')

    def test_extra_rendered_mesh_rejected(self):
        def change(actual):
            meshes=actual['scene']['elements'][0]['meshes']['primitives']
            meshes.append(deepcopy(meshes[0]))
        self.reject(change,'rendered triangle multiset|material')

    def test_missing_native_part_rejected(self):
        def change(actual):
            objects=self.objects(actual,103)
            objects.remove(next(o for o in objects if o['class_name']=='FacetedTopology0'))
        self.reject(change,'native shape/display triangles')

    def test_application_identity_tampering_rejected(self):
        def change(actual):
            cell=next(o for o in self.objects(actual,102) if o['class_name']=='DirectShapeDataCell')
            cell['fields']['m_appDataGUID']='other-application-element'
        self.reject(change,'native application ID')

    def test_nested_application_property_tampering_rejected(self):
        def change(actual):
            entity=next(o for o in self.objects(actual,102) if o['class_name']=='ExtensibleStorageEntity')['fields']
            metadata=json.loads(entity['fields'][2]['raw_value'])
            metadata['application_properties']['nested']['values'][2]=999
            entity['fields'][2]['raw_value']=json.dumps(metadata)
        self.reject(change,'application metadata lost or changed')

    def test_saved_level_elevation_tampering_rejected(self):
        actual=deepcopy(self.level_actual)
        planes=[o for o in self.objects(actual,102) if o['class_name']=='Plane']
        # Change both planes consistently, so this tests the requested elevation,
        # not merely disagreement between two copies.
        for plane in planes:plane['fields']['m_origin'][2]+=1
        with self.assertRaisesRegex(ValueError,'native level elevation differs'):
            verify_level(actual,self.source_graphs,self.level,self.all_ids)

    def test_unresolved_positive_reference_rejected(self):
        def change(actual):
            self.objects(actual,102)[0]['fields']['m_assocLevelId']['m_id']['m_id64']=2**31-1
        self.reject(change,'dangling native element reference')

    def test_header_category_mismatch_rejected(self):
        def change(actual):
            self.objects(actual,101)[0]['fields']['m_categroryId']['m_id']['m_id64']=-2000011
        self.reject(change,'header bounds/category')

    def test_resolvable_wrong_material_style_rejected(self):
        def change(actual):
            mesh=next(o for o in self.objects(actual,103) if o['class_name']=='GPolyMesh')
            # A real existing native ID, not a dangling-reference shortcut.
            mesh['fields']['m_interiorGStyleID']['m_id']['m_id64']=1916
        self.assertIn(1916,self.all_ids)
        self.reject(change,'mesh material|style')

    def test_native_explicit_material_mismatch_rejected(self):
        def change(actual):
            mesh=next(o for o in self.objects(actual,103) if o['class_name']=='GPolyMesh')
            mesh['fields']['m_materialID']['m_id']['m_id64']=1916
        self.reject(change,'mesh material|material')

    def test_rendered_material_identity_mismatch_rejected(self):
        def change(actual):
            materials=actual['scene']['elements'][0]['render_materials']
            materials[next(iter(materials))]['material_id']=1916
        self.reject(change,'material')


_ARCHIVE_SHA256='c8a835760afd603f0588ce5010ce8263808b1d79fd98e8e421c1d16aa9d50e9d'
# gzip-compressed independent reader evidence; original provenance is inside.
_ARCHIVE=(
    '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'
    'Br9u32t9KBFCZcFWKngHqnctrCs7tebIlTaqtoUXt2SeagPIkPG/pjzxlRBaJcrN35uuhxueFX8PXQmABa48hH+Eg42kYpkKeSxQ'
    'ZDfU2JQOSoUst39+t8P2z+vFOiRZ3qbKl6jWB2Ys3u5mkczossFKkSRRS+WxrS1Vrf0w1dpLKC8rKlV7p6U9O3QXNZUbmFFjVeX6'
    'uFWudVoobb2orXelqdcjwPvwdQJOY6QElIjBArDGDuKwn9JPN/xFOs2KG9modS2aKHuppEeU3G5uLsHLQAn+21KIcIDqnvAsSgMV'
    'CVmhR77QB2ptN69WAjWECmkES0HFp/Y3GjKZxrmqkGo5SY4F2xRx4knULBlYxVkjScajRGQ4UI8ov6Om1rc8gOZi/STrCi2U69FI'
    'mG2k1wpx1pVhC0S6SG9VDc5DF4IsUKBrbSgSPAgJEG2tbZMUDR6EBqr9+IKK0Lcqot1EdadFt2F7VIcis41dvtKMHeryVWhn8RtV'
    'm7Bmpu9SbOTbccpvPuhaNtWMjB+UD78ZHXdOw6G0y+WxpZ2u4/GS6ZE8yZIo/R2KjpkyD1g+XdLjbRpMYUKKGntitZVk+ZClE56p'
    'jeWPvkqKrKupyzHvnmWb75u9ZkNa69TJMM1CQJYKQHbULr7dUeniWmZyccOzMYt/+TZhQqv3WshH3ochSm4vt+sXU6aE5Sj5xYDu'
    'MTVy4Qh/8Oj6Rvkv+7iLVrWTefx2MjVy3LFsIrz+JC+YcvnbbGRrV8VGV9G3NWuN7rplmdp/+HP2H0q0K0tspQo13EkZqtibM8QS'
    'e8qSa1VlN28Btynm5dt5N6pVIcrc3diFq9GJbT/NUb60h3BVr/h5pCnDRpD3w7cTAL/7EXhtVzecd4rvIz+f5afnzrGBCFiWvjoP'
    'YTeRu6fxEZbe/DzuxK1G6uDnRz2u6WkyHXut9XwHGztbH7XX2A6ou2nvLKf/TFnND2U158rEeGQTA6Q372Z4TaP2wn+Okil1Bn8b'
    'JdOCdxaAqYMIZturEBG1cp1N9ljNh+hB+oRztcWtwVDBYPmrbYyUWcB8dvhYm3gpItXm+zF2GfZ1WD+2PsU7aFHcyudjznLArBfz'
    'WbBFnRA8MCo142EYYZrkMLs0K3gwAjdocjPKgNGzIBcA1O+C/GEBK1jtgR9n30+9aXDNi1x8nX0rx0i9/3IfLxIN/zur3bpl8ZTP'
    '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'
    'i0nldtxe7/X1Wp9PPmW3jQ/da91v6/tdOzXf7TnH8brnua3HPo7H4/5+Eu+551ujXLPVj3u+zgcQf2h0x3f+bBfvwhs/1H1Y3O7r'
    'ZPL0mNt2f2374/ba74/bePNeffI1sx/j9sj63Nf9dfFm3t/H80dE910fwmPGMH7os4P57vdlzn1MSon3nffmNQdvtnHPMR/hJ8l8'
    'Pt9+EHc+jo+d/O5n+N9+zvN9e93G/vqWH+6Y/fDfT/V83fr9z9eN7328LnP9+fG6/97jdT8/ePb/98Gzr8q2f/2svH+1MPnRCR88'
    'ytFzj3/7zccL9vSzk67I/o6q+C//+9crtd/YxuPGrKd/hK//4F5/ZkL068c//e5JfeCWer/5za9+e/u40fOzi0WWWrZlX47lXK5l'
    'LHMJ/zFLauHv4cNEJch71j0qxsIXTK1LcU4ttbknRR0LX6p1LTUW5kfc1phAcQPZtmXbF77et3Ph/sxskRkJFceeZa9l52/cl/1Y'
    '9nPZr2Ufyz6XY124AEctx7Yc/IOOhYrtuJZjLMdcznU54x4Z57bwST75957LeS3nWChwr3W5sly1XNty7ct1LBc/zrVcY7nmMtaF'
    '6cSohTvT2N1aY5zL4KcdC4Ur31UzbrExt4Wv93ks81wmV8JLwbVY3YWDq0FNnnXvHTmyckVWt+0YvXVH+poxzqvmZfO6eeG8cl46'
    'rx0XL1y9lBe33MWDg3FcQm9M4SKm3N2DcVzHcCG9FYdLGa6lJWO4muFyhuvpAl+4ovawhWua3bgYx2XlVsHBOHcL4dLmcBWKcVzd'
    'cHlzmCvjuMJ8N3IwjoscrrL7j4TrzDfe4ndmTt8A7kvCOK52uNzhejMj5WAclzxc83DRc/lOYRzXPVz4cOWZaXEwjosfrr571oXr'
    'n+FbinFE4P2idzshhRCDt9lMd0A5e9cT+4DsmeBTsri4wJcTB29A8ijyKPIo8ijyoPbgHeq7lHHkUeRR5FFxq5Wzt1txC7/yzey7'
    'ud/O7r3CON/RvqV9T/um9l1NHtwPORi3+b5nHHkUeRR5FHkUeRR5MGHmYNzuhi1+QBjnFi/kUftn95YiD74RORhHHszQFp+RKPLg'
    'S5aDceRR5MGthINx7g1DHkUedfqRYxx5FHkUebglQpFHkUeRR5FHkUddfjYZRx5FHkUeRR5FHu4TUeRR5FHkwZc4B+PIo8ijyKPc'
    'eIY8ijyEzyKPchea6afdjzufd/LwcfyNPNx2hVkmB5968tjIYyOPLX4vMI48vNdu5LGRh0sBG3ls5LGRh201W/kFwjjysLuHmwoH'
    '48hjI4/Nrxm/Z/yi6W8axvld45eN3zZ+3fh9Qx4beWzksZHHtvuVxDjy2MhjI4+NPDbysKlqI4+NPDbysEFsIw/KIA7GkcdGHht5'
    'uIuBzVEbeWzksZ1+yTGOPDby2MhjI4+NPDby2MhjI4+NPLbLb0PGkcdGHht5bOSxkcdGHq6YbOSxkQd3UQ7GkcdGHht5bOSxkcdG'
    'HrbLbOSxkcc2/X71C5ZvWPLYyWMnD+bDHHzNksdOHjt5MJPmW9hvYvcZYhx57OSxk8dOHk5bKQ04GFcSuF/ZjCMPmy8oKTgYRx47'
    'eezksZOHlfO++d3OOPLYyWMnj508dvLwAd3dO4C3AO8BfRNgnLcB7wPeCLwTkMdOHj5baQfKTh774d2CceSxkwfzfQ7Gkcfufknk'
    'sZPHTh776W2FceSxkwezZu4xjCOPnTx28tjJYycP21R28tjJYyePnTx28rD3YiePnTwomTgYN7xRMY48dvLYyWMnj508dvLYXSMg'
    'j5089ukdzVsa9zTyoLjk4LZGHgd5HORxkMdBHkyOuO9572MceRzkcZCHBHuQx0EeB3kc5HGQx1HeJBlHHhbdB3kc5HGQx0EeB3kc'
    '5HGQx7F5N2UceRzkcZDHQR4HeRzkcZDHQR4HeRy7t13GkcdBHgd5UC9yMM57szdn787envv+zDjv0N6ivUeTx0EeB3kc5HGQB0Um'
    'hzdyxpHHQR569EEeB3kc5HGQx0EeB3kwTedgHHkc5HGQx0EeB3kc5GETxkEeB3m49neQx0EeB3lQnHEwjjwO8jjIg5qIg3HTOYST'
    'CGYR5HGSx0keJ3mc5MGMnYPJBHmcbsUVZxuMI4+TPE7yOMmDIoKDceRhtXWSx1lOSxhHHid5nORxksdJHid5nORxkoedK+fm/IVx'
    '5GFjxkkeJ3mc5CHZnORBXc7BuN2JDuPI4ySPkzyoCDkYRx4neZzkcZLHeTgjYhx5nORxksfppMlZk9Mm501OnJw59dSJcU6enD2R'
    'x0keJ3mc5HGSx0keJ3mcl3MsxpHHSR4neZzkcZIHNQ4H48jjJA+b8E7ycC3gJI+TPCgNOBhHHid5UMByMG46a3PaxryNPC7yuMjj'
    'Io+LPC7yENYu8rjI44rzO8aRx0UeF3lc5EFZxsE48rjI4yKPq5wIMo48LvKwx+gij4s8LvK4yOMij4s8rs0ZI+PI4yKPizwu8lA3'
    '3TlLI7/I4yKPa3dqyTjyuMjjIo+LPC7yuMjjIo+LPC7yuA7noIwjj4s8LvK4yOMiDypRDsaRx0Ue1+lklXHkcZHH5XTW+awTWme0'
    'Tmmd0zqp7Vkt45zXksdFHhd5XORxkcdFHhd5XORxDae/jCOPizwu8rjI4yKPizwu8rjI4yKPazpPdqLMTJk8BnkM8rDvcZDHII9B'
    'HoM8BnmMOKNmHHkM8hjkMchjkMcgj0EegzwGeYxy6s048hjk4dOdgzwGeQzyGOQxyGOQx9icozOOPAZ5DPIY5DHIY5DHII/h5njk'
    'MXYn84wjj0EegzwGeQzyGOQxDjfRYxx5jMNZP+PIY5DHII9BHm5EM8hjkMcgj0Ee47Q8YBx5DPIY5DHIY5DHIA9qXQ7Gkce4rCMY'
    'Rx7DQsNKw1LDWsNiw2rDcsN6owsOxpHHII9BHoM8BnkM8hjkMchjkMeYViaWJtQm5DHJY5LHJI9JHpM8JnlM8pjkMWMNwzjymOQx'
    'yWOSh4vYkzwmeUzymOQxy2KHceQxy70FGUcekzyo5DkYRx6TPOZmVcQ48pjkMcljkgclPgfjyGOSxySPuVs+MY48JnlM8pjkMclj'
    'ksckj0kekzzmYZ3FOPKY5DHJY5LHJI9JHpM8JnlM8pinBRnjyGOSh1vgTfKY5DHJY5LHJI9JHpM8JnlM8pjkMcljksckj0kekzwm'
    'ecxhhcc48piWgNaAFoFWgZaB1oEWglaC5DG7HOx60IKwK8IuCbsm7KKwq8IuC7su7MLQynBNl5CeYXG4Wh2uloer9eFqgbj2BpCW'
    'iKs14mqRuFZXnZ5hnSjG8OIZloqrteJqsbhaLarJvHjG1oWqZ1gyrtaMq0XjatW4Wjau1o2rheNq5bhaOq5717aeYfW4Wj6u1o+r'
    'BeRqBblaQq5H70jpGVaR69HlsGdYSK5Wkqul5GotuVpMrlaTq+Xkaj25WlCuZ1fQnmFNuVpUrlaVq2Xlal25WliuVparpeVqbble'
    'XXR7huXlan25WmCuVpirJeZqjblaZK5Wmatl5jq6TvcMK83VUnPtnTUtNlerzdVyc7XeXC0419kbcnZp37W9xb2ZNwO0AzQEtAQ0'
    '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'
    'SlEqRakUpVKUSlEqRakUpVKUSkwqManEpBKTurOnxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk+yh9cUz'
    'XPoWk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQS'
    'k0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pMKjGpxKQSk0pM8rd1+OIZHejsxgQ7E4xWTCoxqcSkEpNKTCoxqcSkSrcyfHoZ'
    'PKO7GbqdofsZuqGhOxq6paF7GmxqSPfoVLc/eIaZi0klJpWYVGJSiUklJpWYVGJSiUklJpWYVGJSiUklJpWYVGJSiUklJpWYVGJS'
    'iUmV/o02Zi4mlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhU'
    'YlKJSSUmlZhkM7AvnmHmYlKJSSUmlZhUYlKJSSUmlZhUYlKJSSUmlZhUYlL1L+oRk3qjj+qulW5b6b6VblzpzpVuXenelW5e6e6V'
    'bl/p/pVuYOkOlm5h6R6WbmLpLpZuY+k+lk8jS3eyfFpZPKObWbqbpdtZup+lG1q6o8XMu6elm1q6q6XbWrqvpRtburOlW1u6t6Wb'
    'W7q7pdtbur+lG1y6w6VbXLrHpZtcusul21y6z6UbXbrTpVtdutelm12626XbXbrfpRteuuOlW17q8/uQPMPMu+2l+1668aU7X7r1'
    'pXtfuvmlu1+6/aX7X7oBpjtgugWme2C6Caa7YLoNpvtguhGmO2G6FaZ7YboZprthuh2m+2G6Iaa7YbodpvthuiGmO2K6JUZH6t7Z'
    'frqqf0tF6UilI5WOVDpS6UilI5WOVDpS6UilI5WOVDpS6UilI5WEVOpRqUelFJVSVEpRbd2j1E1K3aX0aVPyT+lGpe5U6lal7lXq'
    'ZiUDVYpKKSqlqJSiUopKKSqlqJSiUopKKSqlqJSiUopKKSp9qPSh0odKHyp9qPSh0odKHyp9qPSh0odKHyp9qKShUoVKFaqtm5f8'
    'y5ls/7LbYb95Csu2yd8+f/28ffn6c1PqeB9vYfHxft/u7/fxPDYK7mPeua+8H/4Gp/mYvD2fjzdzsue41Xxt/Ld1fTDLedtM/Xmc'
    '8vf9LNevXn/0+dTHf/gbLhcB9mO9j+2533hPDf6Ak2nTe7vNB1PX13vL+3l/vO/v5/vY79S5rzc3pGs8HvW0A/iPr99/s+UOf5Ft'
    'on/xa4AeRPU4+AEer/29Tf5dz/O9bq/ni3/jzXrsvD2e22sb23tj6rY/35P8cr3uc/vFX/5Cg+/+QQ4K3Md1Pq7rVfu73naf8zPk'
    'wVTnYBLxuO8Hf+39TSHHHGV9PG9XHvzAD6bNj9XfN/TVn/3np1x/cT991HzPncnQeD/nneuy13u97RcXbD/u83FQFZy/+PopXs7p'
    'J3f+/g/+7vh/tjv17/pJxC9ujy//xSd6jOOLb6L+hy/sBP7sRv7lF59/wBefh76WL/7weP321b898KuTv/mNgp+9iP70p38Hf7IV'
    'LnEZBQA='
)

if __name__=='__main__':unittest.main()

