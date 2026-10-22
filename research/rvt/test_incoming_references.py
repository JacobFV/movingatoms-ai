import unittest
from incoming_references import typed_hits

class TypedHitsTests(unittest.TestCase):
    def test_declared_types_arrays_inheritance_and_pointer_graph(self):
        def field(name,tag,modifier=0):return {'name':name,'base':14,'modifier':modifier,'references':[{'tag':tag}]}
        def cls(tag,name,fields=(),parent=0):return {'tag':tag,'name':name,'fields':list(fields),'parent_reference':{'tag':parent}}
        declarations=[cls(1,'ElementId'),cls(2,'Base',[field('owner',1)]),
            cls(3,'Derived',[field('refs',1,0x50),field('pointer',1,1)],2),cls(4,'Unrelated',[field('not_id',5)]),cls(5,'IntegerWrapper')]
        ident={'m_id':{'m_id64':20826}}
        graph={'objects':[{'class_tag':3,'class_name':'Derived','fields':{'owner':ident,'refs':[ident], 'pointer':ident}},
                          {'class_tag':4,'class_name':'Unrelated','fields':{'not_id':ident}},
                          {'class_tag':1,'class_name':'ElementId','fields':ident}]}
        hits=typed_hits(graph,declarations,{20826})
        self.assertEqual(len(hits),3)
        self.assertEqual([h['path']for h in hits],['objects[0](Derived).fields.owner','objects[0](Derived).fields.refs[0]','objects[2](ElementId).fields'])
        self.assertEqual(typed_hits(graph,declarations,{80437}),[])

    def test_cycle_is_rejected(self):
        declarations=[{'tag':1,'name':'Bad','parent_reference':{'tag':1},'fields':[]}]
        with self.assertRaisesRegex(ValueError,'cyclic'):
            typed_hits({'objects':[{'class_tag':1,'class_name':'Bad','fields':{}}]},declarations,{1})
