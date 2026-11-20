import unittest
import records
class RecordsTests(unittest.TestCase):
 def test_merge_dedupe_retention(self):
  a={'begin':100000,'map_flag':0,'complete':0}
  b=dict(a,complete=1)
  rows=records.merge_history([a,{'begin':-99999999}],[b],clock=100100)
  self.assertEqual(rows,[b])
 def test_no_warning_means_no_alert(self):self.assertEqual(records.alerts({'cleanWater':'okay','robotError':'none','dirtyWater':None}),{})
 def test_alert_dedup_recovery(self):
  calls=[];send=lambda *a:calls.append(a) or True
  a=records.notify({'cleanWater':'out_of_water'},{},1000,send)
  records.notify({'cleanWater':'out_of_water'},a,2000,send)
  self.assertEqual(len(calls),1)
  a=records.notify({'cleanWater':'okay'},a,3000,send)
  records.notify({'cleanWater':'out_of_water'},a,4000,send)
  self.assertEqual(len(calls),2)
 def test_failed_notification_cooldown(self):
  a=records.notify({'dockError':'error'},{},1000,lambda *a:False)
  calls=[]
  records.notify({'dockError':'error'},a,1050,lambda *a:calls.append(a))
  self.assertEqual(calls,[])
