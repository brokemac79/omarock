import unittest
import path_archive as a
class Archive(unittest.TestCase):
 def cap(self):
  return {'mapAt':'2026-11-20T19:44:00Z','calibration':[{'map':{'x':0,'y':0}}],'layers':{'path':[{'kind':'path','points':[[0,0],[1,1]]}]}}
 def test_empty(self): self.assertEqual(a.merge([],1,{}),[])
 def test_dedupe(self):
  r=a.merge([],1,self.cap());self.assertEqual(len(a.merge(r,1,self.cap())),1)
 def test_floor_isolation(self):
  r=a.merge([],1,self.cap());self.assertEqual(len(a.merge(r,2,self.cap())),2)
 def test_frame_isolation(self):
  r=a.merge([],1,self.cap());c=self.cap();c['calibration']=[{'map':{'x':2,'y':0}}];self.assertEqual(len(a.merge(r,1,c)),2)
 def test_invalid(self):
  c=self.cap();c['layers']['path'][0]['points'][0][0]=float('nan');self.assertEqual(a.merge([],1,c),[])
 def test_bound(self):
  self.assertEqual(len(a.merge([{'digest':str(i)} for i in range(200)],1,self.cap())),120)
