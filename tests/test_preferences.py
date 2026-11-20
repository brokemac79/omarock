import unittest
import preferences
class PreferencesTest(unittest.TestCase):
    maps=[{"id":0,"rooms":[{"id":16}]},{"id":1,"rooms":[{"id":16}]}]
    def value(self,**kw):
        return dict(floor=0,room=16,alias="  Study ",notes=" Local note ",mode="mop",**kw)
    def test_trim(self):
        self.assertEqual(preferences.validate(self.value(),self.maps)["alias"],"Study")
    def test_floor_isolation(self):
        self.assertNotEqual(preferences.key(0,16),preferences.key(1,16))
    def test_reject(self):
        for field,value in [("floor",True),("room",19),("mode","raw"),("alias","x"*81),("notes","x"*1001)]:
            v=self.value();v[field]=value
            with self.assertRaises(ValueError):preferences.validate(v,self.maps)
    def test_fields_whitelisted(self):
        v=self.value();v["command"]="app_start"
        self.assertNotIn("command",preferences.validate(v,self.maps))
