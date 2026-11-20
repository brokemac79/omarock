import unittest
from types import SimpleNamespace
import routines
class RoutineTests(unittest.TestCase):
    def test_known(self):
        self.assertEqual(routines.validate({'id':7,'reviewed':True},[SimpleNamespace(id=7)]),7)
    def test_reject(self):
        for value in [None,{}, {'id':7}, {'id':True,'reviewed':True}, {'id':8,'reviewed':True}]:
            with self.assertRaises(ValueError): routines.validate(value,[SimpleNamespace(id=7)])
