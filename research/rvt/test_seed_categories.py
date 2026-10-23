import json
from copy import deepcopy
from pathlib import Path
import unittest
from seed_categories import context_for

class SeedCategoriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.profile=json.loads((Path(__file__).parent/'results/seed_categories.json').read_text())
    def context(self,kind,**kwargs):return context_for(kind,self.profile,**kwargs)
    def test_measured_categories_aliases_and_materials(self):
        for kind,category,style,material in [('generic',-2000151,413,-1),('wall',-2000011,119,91),('slab',-2000032,229,-1),
            ('door',-2000023,217,-1),('window',-2000014,205,-1),('column',-2000100,303,-1),('beam',-2001320,537,-1),
            ('pipe',-2008044,996,-1),('duct',-2008000,937,-1),('roof',-2000035,237,92),('stairs',-2000120,307,-1),('furniture',-2000080,299,-1)]:
            c=self.context(kind,interior_policy='projection')
            self.assertEqual((c['category_id'],c['style_id'],c['interior_style_id'],c['material_id']),(category,style,style,material))
            self.assertFalse(c['generic_fallback_used'])
    def test_unknown_requires_explicit_fallback(self):
        with self.assertRaisesRegex(ValueError,'unsupported'):self.context('invented category',interior_policy='projection')
        c=self.context('invented category',interior_policy='projection',allow_generic_fallback=True)
        self.assertEqual(c['effective_kind'],'GenericModel');self.assertTrue(c['generic_fallback_used'])
        with self.assertRaisesRegex(ValueError,'boolean'):self.context('invented category',interior_policy='projection',allow_generic_fallback='false')
    def test_cut_is_measured_and_missing_cut_rejected(self):
        self.assertEqual(self.context('wall',interior_policy='cut')['interior_style_id'],120)
        with self.assertRaisesRegex(ValueError,'no measured cut'):self.context('pipe',interior_policy='cut')
    def test_explicit_cross_category_style_and_unresolved_material(self):
        c=self.context('wall',interior_policy='explicit',explicit_interior_style_id=125)
        self.assertEqual(c['interior_category_id'],-2000540)
        with self.assertRaisesRegex(ValueError,'not a verified'):self.context('wall',interior_policy='explicit',explicit_interior_style_id=244)
        with self.assertRaisesRegex(ValueError,'not in seed'):self.context('wall',interior_policy='explicit',explicit_interior_style_id=999999)
    def test_provenance_and_positive_material_validation(self):
        p=deepcopy(self.profile);p['seed_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'provenance'):context_for('wall',p,interior_policy='projection')
        p=deepcopy(self.profile);next(s for s in p['styles']if s['id']==119)['material_id']=999999
        with self.assertRaisesRegex(ValueError,'not a verified'):context_for('wall',p,interior_policy='projection')
    def test_all_advertised_contexts_join_actual_seed_records(self):
        for kind,entry in self.profile['kinds'].items():
            if entry['available']:
                c=self.context(kind,interior_policy='projection')
                self.assertLess(c['category_id'],0);self.assertGreater(c['style_id'],0)
                self.assertEqual(c['native_directshape_category_acceptance'],'unproven')
