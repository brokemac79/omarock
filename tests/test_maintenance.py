import unittest
from maintenance import percentage, validate_reset
class MaintenanceTests(unittest.TestCase):
    def test_percent(self):
        self.assertEqual(percentage(1800,3600),50)
        self.assertEqual(percentage(-10,3600),0)
        self.assertEqual(percentage(7200,3600),100)
    def test_unknown(self):
        for value in (None,True,float("nan"),"5"):
            self.assertIsNone(percentage(value,3600))
        self.assertIsNone(percentage(5,0))
    def test_reset(self):
        self.assertEqual(validate_reset({"consumable":"sensor","afterReplacement":True}),"sensor")
        for plan in ({},None,{"consumable":"filter","afterReplacement":False},{"consumable":"bogus","afterReplacement":True}):
            with self.assertRaises(ValueError): validate_reset(plan)
