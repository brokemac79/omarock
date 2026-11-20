import asyncio
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('omarock',Path(__file__).parents[1]/'omarock.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FakeClient:
    def __init__(self,email):self.email=email;self.requests=0;self.codes=[];self.fail_request=False;self.fail_verify=False
    async def request_code(self):
        self.requests+=1
        if self.fail_request:raise RuntimeError('SECRET-TOKEN-DO-NOT-EXPOSE')
    async def code_login(self,code):
        self.codes.append(code)
        if self.fail_verify:raise RuntimeError('SECRET-TOKEN-DO-NOT-EXPOSE')
        return {'token':'SECRET-SESSION'}
class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def run_flow(self,lines,client=None,store=None):
        events=[];saved=[];c=client or FakeClient('person@example.com');q=iter(lines)
        async def read():return next(q,None)
        def default_store(value,email):saved.append((value,email))
        await m.auth_flow(read,events.append,client_factory=lambda _:c,store=store or default_store)
        return events,saved,c
    async def test_success(self):
        events,saved,c=await self.run_flow([{'email':'person@example.com'},{'code':'123456'}])
        self.assertEqual([e['state'] for e in events],['ready','requesting','code_sent','verifying','signed_in']);self.assertEqual(c.requests,1);self.assertEqual(len(saved),1)
        self.assertNotIn('123456',json.dumps(events));self.assertNotIn('SECRET',json.dumps(events))
    async def test_invalid_email_no_request(self):
        events,saved,c=await self.run_flow([{'email':'not email'}]);self.assertEqual(c.requests,0);self.assertEqual(events[-1]['state'],'error');self.assertFalse(saved)
    async def test_cancel_before_request(self):
        e,s,c=await self.run_flow([{'action':'cancel'}]);self.assertEqual(c.requests,0);self.assertEqual(e[-1]['state'],'cancelled')
    async def test_cancel_after_code(self):
        e,s,c=await self.run_flow([{'email':'p@example.com'},{'action':'cancel'}]);self.assertEqual(e[-1]['state'],'cancelled');self.assertFalse(s)
    async def test_request_failure_sanitized(self):
        c=FakeClient('p@example.com');c.fail_request=True;e,s,c=await self.run_flow([{'email':'p@example.com'}],c);self.assertEqual(e[-1]['state'],'error');self.assertNotIn('SECRET',json.dumps(e));self.assertFalse(s)
    async def test_verification_failure_sanitized(self):
        c=FakeClient('p@example.com');c.fail_verify=True;e,s,c=await self.run_flow([{'email':'p@example.com'},{'code':'123456'},None],c);self.assertNotIn('SECRET',json.dumps(e));self.assertFalse(s)
    async def test_bad_code_does_not_call_api(self):
        e,s,c=await self.run_flow([{'email':'p@example.com'},{'code':'bad'},{'action':'cancel'}]);self.assertEqual(c.codes,[]);self.assertFalse(s)
    async def test_retry_does_not_resend_email(self):
        e,s,c=await self.run_flow([{'email':'p@example.com'},{'code':'bad'},{'code':'123456'}]);self.assertEqual(c.requests,1);self.assertEqual(len(s),1)
    async def test_constructor_failure_sanitized(self):
        events=[]
        async def read():return {'email':'p@example.com'}
        def fail(email):raise ValueError('SECRET-CONSTRUCTOR')
        await m.auth_flow(read,events.append,client_factory=fail)
        self.assertNotIn('SECRET',json.dumps(events));self.assertEqual(events[-1]['state'],'error')
    async def test_timeout(self):
        events=[]
        async def read():await asyncio.sleep(1)
        await m.auth_flow(read,events.append,timeout=.001);self.assertEqual(events[-1]['state'],'expired')
    async def test_save_failure_sanitized(self):
        def fail(*args):raise RuntimeError('SECRET-SESSION')
        e,s,c=await self.run_flow([{'email':'p@example.com'},{'code':'123456'}],store=fail);self.assertEqual(e[-1]['state'],'error');self.assertNotIn('SECRET',json.dumps(e))
class StorageTests(unittest.TestCase):
    def test_private_atomic_save_preserves_parent_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);p.chmod(0o750);target=p/'.roborock';target.write_text('old');m.write_session_file(target,{'user_data':{'token':'sample'}})
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600);self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o750);self.assertEqual(json.loads(target.read_text())['user_data']['token'],'sample');self.assertEqual(len(list(p.iterdir())),1)
    def test_failed_serialization_preserves_old_session(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'.roborock';target.write_text('old')
            with self.assertRaises(TypeError):m.write_session_file(target,object())
            self.assertEqual(target.read_text(),'old');self.assertEqual(len(list(Path(d).iterdir())),1)
    def test_email_and_code_validators(self):
        self.assertEqual(m.validate_email(' p@example.com '),'p@example.com');self.assertEqual(m.validate_code(' 123456 '),'123456')
        for code in ['12345','１２３４５６','1234567','code',None]:
            with self.assertRaises(ValueError):m.validate_code(code)
