import unittest
from types import SimpleNamespace
from dock_controls import validate,ACTIONS
class DockTests(unittest.TestCase):
    def status(self,**kw):
        return SimpleNamespace(**(dict(is_battery_charging=True,in_cleaning=False,in_returning=False,error_code=0,dock_error_status=0,wash_status=0,dry_status=0)|kw))
    def test_review(self):
        with self.assertRaises(ValueError):validate({},self.status(),{'dry':True})
    def test_allowed(self):
        for key in ACTIONS:self.assertEqual(validate({'cycle':key,'reviewed':True},self.status(),{key:True}),key)
    def test_reject(self):
        for kw in [dict(is_battery_charging=False),dict(in_cleaning=True),dict(error_code=1),dict(dock_error_status=1),dict(wash_status=None),dict(dry_status=1)]:
            with self.assertRaises(ValueError):validate({'cycle':'dry','reviewed':True},self.status(**kw),{'dry':True})
        with self.assertRaises(ValueError):validate({'cycle':'raw','reviewed':True},self.status(),{})
