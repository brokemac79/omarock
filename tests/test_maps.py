import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
import omarock as app

class MapImportTests(unittest.IsolatedAsyncioTestCase):
    async def scenario(self, failure=False, busy=False):
        r=app.Robot()
        class Status:
            current_map=1
            in_cleaning=busy
            in_returning=False
            state='charging'
            refresh=AsyncMock()
        class Maps:
            refresh=AsyncMock()
            def as_dict(self): return {'mapInfo':[{'mapFlag':1},{'mapFlag':2},{'mapFlag':3}]}
            async def set_current_map(self,floor): status.current_map=floor; visits.append(floor)
        status=Status();visits=[]
        class V: pass
        r.v=V();r.v.status=status;r.v.maps=Maps()
        async def capture():
            if failure and status.current_map==2: raise ValueError('unavailable')
            return {'mapImage':'image'+str(status.current_map),'mapAt':'now'}
        r.capture_map=capture
        r.snapshot=AsyncMock(return_value={})
        with tempfile.TemporaryDirectory() as tmp, patch.object(app,'STATE',Path(tmp)), patch.object(app.asyncio,'sleep',AsyncMock()):
            if busy:
                with self.assertRaises(ValueError): await r.import_maps()
                self.assertEqual(visits,[]);return
            result=await r.import_maps()
            cache=app.load(Path(tmp)/'floor-maps.json')
            self.assertEqual(status.current_map,1)
            self.assertEqual(visits[-1],1)
            self.assertEqual(set(cache),{'1'} if failure else {'1','2','3'})
            self.assertIn('original selection restored',result['importMessage'])
    async def test_imports_all_and_restores(self): await self.scenario()
    async def test_partial_failure_restores(self): await self.scenario(failure=True)
    async def test_busy_never_switches(self): await self.scenario(busy=True)
