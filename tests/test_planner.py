import unittest
import planner

class PlannerTests(unittest.TestCase):
    maps=[{'id':0,'name':'Downstairs','rooms':[{'id':16,'name':'Kitchen'}]},{'id':1,'name':'Upstairs','rooms':[]}]
    def test_rows_include_floor_and_rooms(self):
        rows=planner.timeline(self.maps,[],{},clock=1000)
        self.assertEqual(len(rows),3)
        self.assertEqual([l['mode'] for l in rows[0]['lanes']],['vacuum','mop'])
    def test_no_invented_completion(self):
        rows=planner.timeline(self.maps,[{'map_flag':0,'area_ids':[],'complete':1}],{},clock=1000)
        self.assertEqual(rows[0]['lanes'][0]['evidenceRuns'],1)
        self.assertEqual(rows[1]['lanes'][0]['evidenceRuns'],0)
        self.assertIsNone(rows[1]['lanes'][0]['last'])
        self.assertEqual(rows[1]['lanes'][0]['status'],'not scheduled')
    def test_due_is_explicit_plan_not_history(self):
        rows=planner.timeline(self.maps,[],{'0:16:mop':{'days':3,'anchor':1000}},clock=1001)
        self.assertEqual(rows[1]['lanes'][1]['due'],260200)
        self.assertIsNone(rows[1]['lanes'][0]['due'])
    def test_validate(self):
        self.assertEqual(planner.validate({'floor':0,'room':16,'mode':'mop','days':7},self.maps)['days'],7)
        for change in [{'room':99},{'floor':True},{'days':-1},{'days':True},{'mode':'both'}]:
            with self.assertRaises(ValueError): planner.validate(dict(floor=0,room=16,mode='mop',days=7)|change,self.maps)

    def test_history_only_on_its_floor_not_rooms(self):
        records=[{'map_flag':0,'begin':100,'end':200,'duration':100,'area':1000000,'complete':1}, {'map_flag':1,'begin':300,'complete':0}, {'map_flag':99,'begin':400}, {'map_flag':0,'begin':None}]
        rows=planner.timeline(self.maps,records,{},clock=1000)
        self.assertEqual(len(rows[0]['activity']),1)
        self.assertEqual(rows[0]['activity'][0]['begin'],100)
        self.assertEqual(rows[1]['activity'],[])
        self.assertEqual(rows[2]['activity'][0]['complete'],0)
        self.assertIsNone(rows[0]['lanes'][0]['last'])
