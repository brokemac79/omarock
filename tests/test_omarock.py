import copy
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('omarock',Path(__file__).parents[1]/'omarock.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot={'activeFloor':0,'maps':[{'id':0,'rooms':[{'id':1},{'id':4}]},{'id':1,'rooms':[{'id':1}]}],'calibration':[1,2,3]}
        self.plan={'floor':0,'confirmedFloor':0,'mode':'vacuum','scope':'rooms','rooms':[4],'passes':1}
    def test_valid_room(self):self.assertEqual(m.validate_plan(self.plan,self.snapshot)['rooms'],[4])
    def test_duplicate_rooms(self):self.plan['rooms']=[4,4];self.assertEqual(m.validate_plan(self.plan,self.snapshot)['rooms'],[4])
    def test_wrong_floor(self):self.plan['floor']=1;self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_confirmation(self):self.plan.pop('confirmedFloor');self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_bad_room(self):self.plan['rooms']=[99];self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_empty_room(self):self.plan['rooms']=[];self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_invalid_mode(self):self.plan['mode']='app_start';self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_invalid_passes(self):
        for n in [0,4,True,'2']:self.plan['passes']=n;self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_floor(self):self.plan['scope']='floor';self.assertEqual(m.validate_plan(self.plan,self.snapshot)['scope'],'floor')
    def test_repeat_floor(self):self.plan.update(scope='floor',passes=2);self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_zone(self):self.plan.update(scope='zone',zones=[[100,200,400,600]]);self.assertEqual(len(m.validate_plan(self.plan,self.snapshot)['zones']),1)
    def test_nan_zone(self):self.plan.update(scope='zone',zones=[[0,0,float('nan'),400]]);self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_no_calibration(self):self.plan.update(scope='zone',zones=[[0,0,400,400]]);self.snapshot.pop('calibration');self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_tiny_zone(self):self.plan.update(scope='zone',zones=[[0,0,5,400]]);self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_many_zones(self):self.plan.update(scope='zone',zones=[[0,0,400,400]]*6);self.assertRaises(ValueError,m.validate_plan,self.plan,self.snapshot)
    def test_no_io_mutation(self):p=copy.deepcopy(self.plan);m.validate_plan(p,self.snapshot);self.assertEqual(p,self.plan)
if __name__=='__main__':unittest.main()

class CachedTests(unittest.TestCase):
    def test_cached_robot_error_is_not_helper_failure(self):
        import json,os,subprocess,sys,tempfile
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/'omarock';state.mkdir();(state/'snapshot.json').write_text(json.dumps({'error':'none','battery':100}))
            env=dict(os.environ,HOME=tmp,XDG_STATE_HOME=tmp,XDG_CONFIG_HOME=tmp)
            result=subprocess.run([sys.executable,str(Path(m.__file__)),'cached'],env=env,capture_output=True,text=True,check=True)
            value=json.loads(result.stdout)
            self.assertNotIn('error',value);self.assertEqual(value['robotError'],'none');self.assertEqual(value['battery'],100)
    def test_cached_no_snapshot_is_honest(self):
        import json,os,subprocess,sys,tempfile
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,str(Path(m.__file__)),'cached'],env=dict(os.environ,HOME=tmp,XDG_STATE_HOME=tmp,XDG_CONFIG_HOME=tmp),capture_output=True,text=True,check=True)
            value=json.loads(result.stdout);self.assertFalse(value['authPresent']);self.assertNotIn('battery',value)
