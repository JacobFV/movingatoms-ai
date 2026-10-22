import unittest
from increment_routing import route

class IncrementRoutingTests(unittest.TestCase):
    def test_terminal_zero_redirect_and_retained_population(self):
        rows=[{'greatest_episode':2,'stored_elements':0,'redirects':[[-1,12],[1,0]]},
              {'greatest_episode':3,'stored_elements':15,'redirects':[[-1,15]]}]
        self.assertEqual(route(1,rows,{1}),1)
        rows[0]['stored_elements']=3;rows[0]['redirects'][-1][1]=3
        self.assertEqual(route(1,rows,{0,1}),0)
        with self.assertRaises(ValueError):route(1,rows,{1})
        with self.assertRaises(ValueError):route(4,rows,{0,1})

    def test_invalid_redirects_are_not_guessed(self):
        for redirects in ([],[[0,0]],[[-1,3],[1,4]],[[-1,3],[1,1]]):
            rows=[{'greatest_episode':0,'stored_elements':0,'redirects':redirects},
                  {'greatest_episode':1,'stored_elements':1,'redirects':[[-1,1]]}]
            with self.assertRaises(ValueError):route(0,rows,{1})
