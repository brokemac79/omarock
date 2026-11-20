import unittest
from device_settings import validate
class SettingsTests(unittest.TestCase):
    def test_valid(self):
        for key,value in [('volume',0),('volume',100),('dnd',True),('child_lock',False)]:
            self.assertEqual(validate(dict(setting=key,value=value,reviewed=True)),(key,value))
    def test_reject(self):
        for key,value in [('volume',True),('volume',-1),('volume',101),('volume',50.5),('dnd',1),('child_lock','false'),('raw','x')]:
            with self.assertRaises(ValueError): validate(dict(setting=key,value=value,reviewed=True))
    def test_review(self):
        with self.assertRaises(ValueError): validate(dict(setting='volume',value=50))
