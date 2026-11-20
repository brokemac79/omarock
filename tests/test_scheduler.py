import unittest,datetime as dt
from unittest.mock import AsyncMock
import scheduler

class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    maps=[{'id':0,'name':'Ground','rooms':[{'id':16,'name':'Kitchen'}]}]
    def plan(self,**kw):return dict(floor=0,room=16,mode='vacuum',hour=10,minute=30,weekdays=[4],enabled=False)|kw
    def test_locked_activation_and_validation(self):
        with self.assertRaises(ValueError):scheduler.validate(self.plan(enabled=True,confirmed=True),self.maps,False)
        self.assertFalse(scheduler.validate(self.plan(),self.maps)['enabled'])
        for change in [{'hour':24},{'minute':True},{'weekdays':[]},{'room':99}]:
            with self.assertRaises(ValueError):scheduler.validate(self.plan(**change),self.maps)
    async def test_due_once_and_no_catchup(self):
        s=scheduler.validate(self.plan(enabled=True,confirmed=True),self.maps,True)
        clock=dt.datetime(2026,11,20,10,30,tzinfo=dt.timezone.utc)
        journal={};dispatch=AsyncMock();persist=lambda j:None
        await scheduler.tick({'a':s},journal,clock,dispatch,persist)
        await scheduler.tick({'a':s},journal,clock,dispatch,persist)
        await scheduler.tick({'a':s},{},clock+dt.timedelta(minutes=2),dispatch,persist)
        dispatch.assert_awaited_once()
    async def test_uncertain_not_retried(self):
        s=scheduler.validate(self.plan(enabled=True,confirmed=True),self.maps,True)
        journal={};dispatch=AsyncMock(side_effect=TimeoutError('timeout'));clock=dt.datetime(2026,11,20,10,30,tzinfo=dt.timezone.utc)
        await scheduler.tick({'a':s},journal,clock,dispatch,lambda j:None)
        await scheduler.tick({'a':s},journal,clock,dispatch,lambda j:None)
        dispatch.assert_awaited_once()
    def test_dst_duplicate_slot(self):
        s=scheduler.validate(self.plan(hour=1,weekdays=[6],enabled=True,confirmed=True),self.maps,True)
        a=dt.datetime(2026,10,25,0,30,tzinfo=dt.timezone.utc)
        self.assertEqual(scheduler.slot(s,a),scheduler.slot(s,a+dt.timedelta(hours=1)))
