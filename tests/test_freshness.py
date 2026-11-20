import unittest
import freshness
class Freshness(unittest.TestCase):
 def setUp(self):
  self.maps=[{'id':1,'rooms':[{'id':16}]},{'id':2,'rooms':[{'id':16}]}]
  self.record={'map_flag':1,'area_ids':[16],'complete':True,'end':100000}
 def row(self,records):
  return freshness.summarize(self.maps,records,200000)['1']['16']
 def test_explicit(self):
  r=self.row([self.record]);self.assertEqual(r['last'],100000);self.assertEqual(r['ageDays'],1);self.assertEqual(r['mode'],'unknown');self.assertEqual(r['coverage'],'unverified')
 def test_floor_isolation(self):
  self.assertIsNone(freshness.summarize(self.maps,[self.record],200000)['2']['16']['last'])
 def test_blank_ids_not_whole_floor(self):
  self.assertIsNone(self.row([dict(self.record,area_ids=[])])['last'])
 def test_incomplete(self):
  self.assertIsNone(self.row([dict(self.record,complete=False)])['last'])
 def test_invalid_future(self):
  for value in [True,'100000',float('nan'),300000,-1]:
   self.assertIsNone(self.row([dict(self.record,end=value)])['last'])
 def test_strict_ids(self):
  for change in [{'map_flag':True},{'area_ids':['16']},{'area_ids':None}]:
   self.assertIsNone(self.row([dict(self.record,**change)])['last'])
 def test_newest(self):
  self.assertEqual(self.row([self.record,dict(self.record,end=190000)])['last'],190000)
