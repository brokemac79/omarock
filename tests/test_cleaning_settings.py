import unittest
from types import SimpleNamespace
import cleaning_settings as c
class CleaningSettingsTests(unittest.TestCase):
 def setUp(self): self.s=SimpleNamespace(fan_speed_mapping={101:'Quiet',102:'Balanced'},fan_power=102)
 def test_options(self):
  self.assertEqual(list(c.snapshot(self.s)),['suction'])
  self.assertEqual(c.validate(dict(setting='suction',value=101,reviewed=True),self.s),('SET_CUSTOM_MODE',101))
 def test_reject(self):
  for key,value in [('raw',101),('suction',True),('suction',999),('water',101),('suction','101')]:
   with self.assertRaises(ValueError): c.validate(dict(setting=key,value=value,reviewed=True),self.s)
 def test_review_and_unknown_current(self):
  with self.assertRaises(ValueError): c.validate(dict(setting='suction',value=101),self.s)
  self.s.fan_power=None
  self.assertEqual(c.snapshot(self.s),{})
