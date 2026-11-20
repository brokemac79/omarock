#!/usr/bin/env python3
"""OmaRock native desktop app helper. No web service."""
import argparse
import asyncio
import base64
import datetime as dt
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'omarock'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'omarock'

def private_dir(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)

def save(path, value):
    private_dir(path.parent)
    tmp = path.with_suffix(path.suffix+'.tmp')
    fd = os.open(tmp, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f)
    os.replace(tmp, path)

def load(path, default=None):
    try: return json.loads(path.read_text())
    except (OSError, ValueError): return default

def enum_name(x):
    return getattr(x, 'name', x)

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()

def validate_plan(plan, snapshot):
    """Pure, fail-closed request validation; no device I/O."""
    if not isinstance(plan, dict): raise ValueError('Expected an object')
    floor = plan.get('floor')
    maps = snapshot.get('maps', [])
    selected = next((m for m in maps if m['id'] == floor), None)
    if type(floor) is not int or selected is None: raise ValueError('Unknown floor')
    if floor != snapshot.get('activeFloor'): raise ValueError('Robot must already be on this floor; move it and select its map in the Roborock app first')
    if type(plan.get('confirmedFloor')) is not int or plan.get('confirmedFloor') != floor: raise ValueError('Confirm the physical floor')
    if plan.get('mode') not in ('vacuum', 'mop', 'vacuum_and_mop'): raise ValueError('Unsupported cleaning mode')
    passes = plan.get('passes', 1)
    if type(passes) is not int or not 1 <= passes <= 3: raise ValueError('Passes must be 1–3')
    scope = plan.get('scope')
    result = dict(plan)
    if scope == 'rooms':
        ids = plan.get('rooms', [])
        valid = {r['id'] for r in selected['rooms']}
        if not ids or any(type(i) is not int or i not in valid for i in ids): raise ValueError('Select valid rooms')
        result['rooms'] = sorted(set(ids))
    elif scope == 'floor':
        if passes != 1: raise ValueError('Whole-floor repeat passes are not yet supported; select rooms instead')
    elif scope == 'zone':
        zones = plan.get('zones', [])
        if not 1 <= len(zones) <= 5: raise ValueError('Draw one to five zones')
        if not snapshot.get('calibration'): raise ValueError('Map coordinates unavailable')
        for zone in zones:
            if not isinstance(zone, list) or len(zone) != 4 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>100000 for v in zone): raise ValueError('Invalid zone coordinates')
            if zone[2]-zone[0]<100 or zone[3]-zone[1]<100: raise ValueError('Zone must be at least 10 cm across')
    else: raise ValueError('Unknown cleaning scope')
    return result

class Robot:
    def __init__(self):
        self.config = load(CONFIG/'config.json', {})
    async def connect(self):
        # Reuse the vendor CLI's credential format; credentials never enter the repo.
        from roborock.cli import RoborockContext
        self.context = RoborockContext()
        manager = await self.context.get_device_manager()
        await manager.ensure_device_manager()
        devices = list(manager._devices.values())
        device_id = self.config.get('device_id')
        if device_id:
            device = await manager.get_device(device_id)
        elif len(devices)==1:
            device = devices[0]
        else: raise ValueError('Set device_id in ~/.config/omarock/config.json; multiple or no devices found')
        if not device.v1_properties: raise ValueError('Only Roborock V1 devices are supported in this alpha')
        self.name = device.name
        self.v = device.v1_properties
        await self.v.start()
    async def close(self):
        if hasattr(self,'context'): await self.context.cleanup()
    async def snapshot(self, include_map=False):
        await self.v.status.refresh()
        s=self.v.status
        result={'at':now(),'name':self.name,'demo':False,'battery':s.battery,'state':enum_name(s.state),
                'activeFloor':s.current_map,'robotError':enum_name(s.error_code),'dockError':enum_name(s.dock_error_status),
                'cleanWater':enum_name(s.clear_water_box_status),'dirtyWater':enum_name(s.dirty_water_box_status),
                'washing':s.wash_status,'drying':s.dry_status,'drySeconds':s.rdt,
                'mode':s.current_cleaning_mode_name,'controlsEnabled':self.config.get('allow_control') is True,
                'tankNote':'Flags, not fill levels. Clean tank removal verified; dirty tank unverified.'}
        errors=[]
        for label,trait in [('maps',self.v.maps),('consumables',self.v.consumables),('history',self.v.clean_summary)]:
            try:
                await trait.refresh()
                if label=='maps':
                    raw=trait.as_dict()
                    result['maps']=[{'id':m.get('mapFlag'),'name':m.get('name', 'Floor'), 'rooms':[{'id':r['id'],'name':r.get('iotName') or 'Room '+str(r['id'])} for r in m.get('rooms',[])]} for m in raw.get('mapInfo',[])]
                elif label=='consumables':
                    result['consumables']={k:(round(max(0,getattr(trait,k+'_time_left'))/3600,1) if getattr(trait,k+'_time_left',None) is not None else None) for k in ['main_brush','side_brush','filter','sensor']}
                    import maintenance
                    from roborock.data import Consumable
                    constants=Consumable.main_brush_time_left.fget.__globals__
                    lifetimes={'main_brush':'MAIN_BRUSH_REPLACE_TIME','side_brush':'SIDE_BRUSH_REPLACE_TIME','filter':'FILTER_REPLACE_TIME','sensor':'SENSOR_DIRTY_REPLACE_TIME'}
                    result['maintenance']={k:{'percent':maintenance.percentage(getattr(trait,k+'_time_left',None),constants[c]),'supported':getattr(trait,maintenance.FIELDS[k],None) is not None} for k,c in lifetimes.items()}
                else:
                    result['totalRuns']=trait.clean_count
                    result['history']=[]
                    for record_id in sorted(trait.records or [], reverse=True)[:10]:
                        try:
                            raw=await self.v.command.send('get_clean_record',[record_id])
                            for rec in raw if isinstance(raw,list) else [raw]:
                                if isinstance(rec,dict):
                                    result['history'].append({k:rec.get(k) for k in ['begin','end','duration','area','complete','map_flag','area_ids','wash_count','clean_type']})
                        except Exception: errors.append('One history record unavailable')
            except Exception: errors.append(label+' unavailable')
        try:
            result['routines']=[{'id':r.id,'name':r.name} for r in await self.v.routines.get_routines()]
            result['routinesAvailable']=True
        except Exception:
            result['routinesAvailable']=False
            errors.append('Routines unavailable')
        import cleaning_settings
        result['cleaningSettings']=cleaning_settings.snapshot(s)
        result['deviceSettings']={}
        for key,attribute in [('volume','sound_volume'),('dnd','dnd'),('child_lock','child_lock')]:
            try:
                trait=getattr(self.v,attribute)
                await trait.refresh()
                if key=='volume':
                    value=trait.volume
                    if type(value) is not int or not 0<=value<=100: raise ValueError('Unavailable')
                    row={'value':value}
                elif key=='dnd':
                    if trait.enabled not in (0,1): raise ValueError('Unavailable')
                    row={'value':trait.is_on,'startHour':trait.start_hour,'startMinute':trait.start_minute,'endHour':trait.end_hour,'endMinute':trait.end_minute}
                else:
                    if trait.lock_status not in (0,1): raise ValueError('Unavailable')
                    row={'value':trait.is_on}
                result['deviceSettings'][key]=row
            except Exception:
                errors.append(key+' setting unavailable')
        cached=load(STATE/'floor-maps.json',{})
        key=str(result['activeFloor'])
        if include_map or key not in cached:
            try:
                cached[key]=await self.capture_map()
                save(STATE/'floor-maps.json',cached)
            except Exception: errors.append('Map unavailable')
        result['floorMaps']=cached
        result.update(cached.get(key,{}))
        import records,time,subprocess
        archived=records.merge_history(load(STATE/'history.json',[]),result.get('history',[]))
        save(STATE/'history.json',archived)
        result['historyArchive']=archived
        result['alerts']=records.alerts(result)
        if self.config.get('desktop_notifications',True):
            def send(title,message):
                try: return subprocess.run(['notify-send','--app-name=OmaRock',title,message],timeout=5,capture_output=True).returncode==0
                except (OSError,subprocess.TimeoutExpired): return False
            save(STATE/'alerts.json',records.notify(result,load(STATE/'alerts.json',{}),time.time(),send))
        result['warnings']=errors
        return result
    async def capture_map(self):
        result={}
        await self.v.map_content.refresh()
        content=self.v.map_content
        if content.image_content:
            from PIL import Image, ImageChops
            import io
            image=Image.open(io.BytesIO(content.image_content)).convert('RGB')
            bg=Image.new('RGB',image.size,image.getpixel((0,0)))
            bounds=ImageChops.difference(image,bg).getbbox()
            calibration=content.map_data.calibration()
            if bounds:
                left,top,right,bottom=bounds
                left=max(0,left-40);top=max(0,top-40)
                image=image.crop((left,top,min(image.width,right+40),min(image.height,bottom+40)))
                for point in calibration or []:
                    point['map']['x']-=left;point['map']['y']-=top
            out=io.BytesIO();image.save(out,format='PNG')
            result['mapImage']='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
            result['calibration']=calibration
        if not result.get('mapImage'): raise ValueError('Map image unavailable')
        result['mapAt']=now()
        return result

    async def idle(self):
        await self.v.status.refresh()
        if self.v.status.in_cleaning or self.v.status.in_returning or enum_name(self.v.status.state) not in ('charging','idle','fully_charged'):
            raise ValueError('Map import requires an idle or charging robot')

    async def select_map(self, floor):
        await self.idle()
        await self.v.maps.set_current_map(floor)
        await asyncio.sleep(3)
        await self.v.status.refresh()
        if self.v.status.current_map != floor: raise ValueError('Map selection not confirmed')

    async def import_maps(self):
        await self.idle()
        original=self.v.status.current_map
        await self.v.maps.refresh()
        ids=[m['mapFlag'] for m in self.v.maps.as_dict().get('mapInfo',[])]
        if type(original) is not int or original not in ids: raise ValueError('Original map is unknown; import cancelled')
        cached=load(STATE/'floor-maps.json',{})
        failures=[]
        try:
            for floor in ids:
                try:
                    await self.select_map(floor)
                    cached[str(floor)]=await self.capture_map()
                    save(STATE/'floor-maps.json',cached)
                except Exception as error:
                    failures.append('Floor '+str(floor)+': '+str(error)[:100])
                    break
        finally:
            try:
                await self.v.status.refresh()
                if self.v.status.current_map != original: await self.select_map(original)
                await self.v.status.refresh()
                if self.v.status.current_map != original: raise ValueError('Original map not confirmed')
            except Exception as error:
                raise ValueError('Import stopped. Original floor restoration could not be confirmed: '+str(error)[:100])
        result=await self.snapshot(include_map=True)
        result['importMessage']=('Imported '+str(len(cached))+' floor maps; original selection restored.' if not failures else '; '.join(failures)+'; original selection restored.')
        return result

    async def execute(self, action, plan=None):
        if self.config.get('allow_control') is not True: raise ValueError('Control locked. Explicitly enable allow_control in your private config after supervised testing')
        await self.v.status.refresh()
        if action=='cleaning-setting':
            import cleaning_settings
            from roborock.roborock_typing import RoborockCommand
            command,value=cleaning_settings.validate(plan,self.v.status)
            if self.v.status.in_cleaning or self.v.status.in_returning: raise ValueError('Robot busy')
            if self.v.status.error_code or self.v.status.dock_error_status: raise ValueError('Resolve robot/dock warnings first')
            await self.v.command.send(getattr(RoborockCommand,command),[value])
            return 'Preference submitted; refresh to verify'
        if action=='setting':
            import device_settings
            key,value=device_settings.validate(plan)
            if self.v.status.in_cleaning or self.v.status.in_returning: raise ValueError('Robot busy')
            trait=getattr(self.v,{'volume':'sound_volume','dnd':'dnd','child_lock':'child_lock'}[key])
            await trait.refresh()
            if key=='volume':
                if trait.volume is None: raise ValueError('Volume unavailable')
                await trait.set_volume(value)
            else:
                if key=='dnd':
                    if trait.enabled not in (0,1): raise ValueError('DND unavailable')
                    if value and not all(type(v) is int and 0<=v<limit for v,limit in [(trait.start_hour,24),(trait.end_hour,24),(trait.start_minute,60),(trait.end_minute,60)]):
                        raise ValueError('Set a valid DND time window in the official app first')
                elif trait.lock_status not in (0,1): raise ValueError('Child lock unavailable')
                await (trait.enable() if value else trait.disable())
            return 'Setting submitted; refresh to verify'
        if action=='routine':
            import routines
            identifier=routines.validate(plan,await self.v.routines.get_routines())
            if self.v.status.in_cleaning or self.v.status.in_returning:
                raise ValueError('Robot busy')
            if (self.v.status.battery or 0)<20 or self.v.status.error_code or self.v.status.dock_error_status:
                raise ValueError('Resolve battery or robot/dock warnings first')
            await self.v.routines.execute_routine(identifier)
            return 'Routine submitted; completion unverified'
        if action=='reset-consumable':
            import maintenance
            from roborock.devices.traits.v1.consumeable import ConsumableAttribute
            key=maintenance.validate_reset(plan)
            await self.v.consumables.refresh()
            if getattr(self.v.consumables,maintenance.FIELDS[key],None) is None:
                raise ValueError('Consumable unsupported or unavailable')
            if self.v.status.in_cleaning or self.v.status.in_returning:
                raise ValueError('Robot busy')
            await self.v.consumables.reset_consumable(ConsumableAttribute.from_str(maintenance.FIELDS[key]))
            return 'Usage reset submitted; refresh to verify'
        if action in ('pause','dock'):
            return await self.v.command.send('app_pause' if action=='pause' else 'app_charge')
        if action!='clean': raise ValueError('Unknown action')
        # Refresh the map list before validating room IDs; never silently switch floors.
        await self.v.maps.refresh()
        snapshot=load(STATE/'snapshot.json',{})
        snapshot['activeFloor']=self.v.status.current_map
        raw=self.v.maps.as_dict()
        snapshot['maps']=[{'id':m['mapFlag'],'rooms':m.get('rooms',[])} for m in raw.get('mapInfo',[])]
        plan=validate_plan(plan,snapshot)
        if self.v.status.in_cleaning or self.v.status.in_returning: raise ValueError('Robot busy; pause or finish current task first')
        if (self.v.status.battery or 0)<20: raise ValueError('Battery below 20%')
        if self.v.status.error_code or self.v.status.dock_error_status: raise ValueError('Resolve robot/dock errors first')
        modes={'vacuum':'vacuum','mop':'mop','vacuum_and_mop':'vac_and_mop'}
        await self.v.status.set_cleaning_mode(modes[plan['mode']])
        if plan['scope']=='rooms':
            response=await self.v.command.send('app_segment_clean',[{'segments':plan['rooms'],'repeat':plan['passes']}])
        elif plan['scope']=='zone':
            response=await self.v.command.send('app_zoned_clean',[[round(v) for v in z]+[plan['passes']] for z in plan['zones']])
        else: response=await self.v.command.send('app_start')
        # This records intent only, never a claim that the room was cleaned.
        with open(STATE/'requests.jsonl','a') as f: f.write(json.dumps({'at':now(),'plan':plan,'result':'submitted, completion unverified'})+'\n')
        return response

async def perform(operation, **kwargs):
    robot=Robot()
    try:
        await robot.connect()
        if operation=='snapshot': return await robot.snapshot(**kwargs)
        if operation=='import-maps': return await robot.import_maps()
        return await robot.execute(operation,**kwargs)
    finally: await robot.close()

class AuthInputError(ValueError):
    pass

def validate_email(value):
    if not isinstance(value,str): raise AuthInputError('Enter your Roborock account email address.')
    value=value.strip()
    if len(value)>254 or not re.fullmatch(r"[^\s@]{1,64}@[^\s@]+\.[^\s@]+",value):
        raise AuthInputError('Enter a valid email address.')
    return value

def validate_code(value):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9]{6}",value.strip()):
        raise AuthInputError('Enter the six-digit email code.')
    return value.strip()

def write_session_file(path,value):
    import tempfile
    path=Path(path)
    name=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix='.omarock-session-',delete=False) as stream:
            name=stream.name
            os.chmod(name,0o600)
            json.dump(value,stream)
        os.replace(name,path)
        os.chmod(path,0o600)
    finally:
        if name and os.path.exists(name):os.unlink(name)

def store_session(user_data,email):
    from roborock.cli import ConnectionCache, RoborockContext
    # Same account-cache format as the vendor CLI, atomic write with mode 0600.
    write_session_file(RoborockContext.roborock_file,ConnectionCache(user_data=user_data,email=email).as_dict())

async def auth_flow(read,emit,client_factory=None,store=None,timeout=300):
    """Private JSON-lines over stdin/stdout; never echo codes or tokens."""
    store=store or store_session
    emit({'state':'ready'})
    try:
        request=await asyncio.wait_for(read(),timeout)
        if not request or request.get('action')=='cancel':
            emit({'state':'cancelled'});return
        email=validate_email(request.get('email'))
        if client_factory is None:
            from roborock.web_api import RoborockApiClient
            client_factory=RoborockApiClient
        client=client_factory(email)
        emit({'state':'requesting','message':'Requesting your verification code…'})
        try: await asyncio.wait_for(client.request_code(),45)
        except Exception:
            emit({'state':'error','message':'Could not request a code. Check your email and internet connection; if you requested one recently, wait before trying again.'});return
        emit({'state':'code_sent','message':'Check your email for the six-digit Roborock code.'})
        for attempt in range(3):
            request=await asyncio.wait_for(read(),timeout)
            if not request or request.get('action')=='cancel':
                emit({'state':'cancelled'});return
            try:code=validate_code(request.get('code'))
            except AuthInputError as error:
                emit({'state':'code_sent','message':str(error)});continue
            emit({'state':'verifying','message':'Verifying your code…'})
            try:user_data=await asyncio.wait_for(client.code_login(code),45)
            except Exception:
                emit({'state':'code_sent','message':'Code not accepted or verification unavailable. Check the code and try again, or cancel and request a new one.'});continue
            finally:code=None
            try:store(user_data,email)
            except Exception:
                emit({'state':'error','message':'Sign-in succeeded, but the session could not be saved. Check permissions for your home directory.'});return
            emit({'state':'signed_in','message':'Signed in. Loading your robot…'});return
        emit({'state':'error','message':'Too many unsuccessful attempts. Cancel and request a new code when ready.'})
    except asyncio.TimeoutError:
        emit({'state':'expired','message':'Sign-in timed out. Request a new code when ready.'})
    except AuthInputError as error:
        emit({'state':'error','message':str(error)})
    except Exception:
        emit({'state':'error','message':'Sign-in could not finish. Cancel and try again.'})

async def auth_stdio():
    import logging
    # Never forward vendor authentication logging or exception payloads.
    logging.disable(logging.CRITICAL)
    reader=asyncio.StreamReader(limit=4096)
    protocol=asyncio.StreamReaderProtocol(reader)
    transport,_=await asyncio.get_running_loop().connect_read_pipe(lambda:protocol,sys.stdin.buffer)
    async def read():
        line=await reader.readline()
        if not line:return None
        try:value=json.loads(line)
        except (ValueError,UnicodeError):raise AuthInputError('Invalid sign-in request')
        if not isinstance(value,dict):raise AuthInputError('Invalid sign-in request')
        return value
    def emit(value): print(json.dumps(value),flush=True)
    try:await auth_flow(read,emit)
    finally:transport.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['snapshot','cached','bar','action','auth','import-maps','planner','save-plan','schedules','save-schedule','delete-schedule','scheduler-tick','room-preferences','save-room-preference'])
    parser.add_argument('--request',default='{}')
    args=parser.parse_args()
    private_dir(STATE);private_dir(CONFIG)
    if args.command=='auth':
        os.umask(0o077)
        asyncio.run(auth_stdio());return
    try:
        if args.command in ('snapshot','import-maps','action','scheduler-tick','save-schedule','delete-schedule'):
            import fcntl
            lock=open(STATE/'device.lock','w')
            try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise ValueError('Another device operation is running; try again shortly')
        if args.command in ('room-preferences','save-room-preference'):
            import preferences
            values=load(STATE/'room-preferences.json',{})
            if args.command=='save-room-preference':
                value=preferences.validate(json.loads(args.request),load(STATE/'snapshot.json',{}).get('maps',[]))
                values[preferences.key(value['floor'],value['room'])]=value
                save(STATE/'room-preferences.json',values)
            result={'preferences':values}
        elif args.command in ('schedules','save-schedule','delete-schedule'):
            import scheduler,uuid
            schedules=load(STATE/'schedules.json',{})
            request=json.loads(args.request)
            if args.command=='save-schedule':
                snapshot=load(STATE/'snapshot.json',{})
                config=load(CONFIG/'config.json',{})
                value=scheduler.validate(request,snapshot.get('maps',[]),config.get('allow_control') is True)
                schedules[uuid.uuid4().hex]=value
                save(STATE/'schedules.json',schedules)
            elif args.command=='delete-schedule':
                schedules.pop(request.get('id'),None)
                save(STATE/'schedules.json',schedules)
            result={'schedules':[dict(v,id=k) for k,v in schedules.items()],'controlsEnabled':load(CONFIG/'config.json',{}).get('allow_control') is True,'outcomes':list(load(STATE/'schedule-journal.json',{}).values())[-10:]}
        elif args.command=='scheduler-tick':
            import scheduler
            journal=load(STATE/'schedule-journal.json',{})
            async def dispatch(schedule):
                plan={'floor':schedule['floor'],'confirmedFloor':schedule['floor'],'mode':schedule['mode'],'passes':1,'scope':'floor' if schedule['room'] is None else 'rooms','rooms':[] if schedule['room'] is None else [schedule['room']]}
                # execute rechecks current map, busy, battery, errors and control lock.
                # Never switches floor maps or wakes a sleeping desktop.
                return await perform('clean',plan=plan)
            result={'outcomes':asyncio.run(scheduler.tick(load(STATE/'schedules.json',{}),journal,dt.datetime.now(dt.timezone.utc),dispatch,lambda j:save(STATE/'schedule-journal.json',j)))}
        elif args.command=='import-maps':
            if json.loads(args.request).get('confirmed') is not True: raise ValueError('Explicit map-import confirmation required')
            result=asyncio.run(perform('import-maps'))
            save(STATE/'snapshot.json',result)
        elif args.command=='snapshot':
            result=asyncio.run(perform('snapshot',include_map=True))
            save(STATE/'snapshot.json',result)
        elif args.command in ('planner','save-plan'):
            import planner
            snapshot=load(STATE/'snapshot.json',{})
            plans=load(STATE/'plans.json',{})
            if args.command=='save-plan':
                plan=planner.validate(json.loads(args.request),snapshot.get('maps',[]))
                plan['anchor']=dt.datetime.now(dt.timezone.utc).timestamp()
                plans[planner.key(plan['floor'],plan['room'],plan['mode'])]=plan
                save(STATE/'plans.json',plans)
            result={'rows':planner.timeline(snapshot.get('maps',[]),snapshot.get('history',[]),plans)}
        elif args.command=='action':
            request=json.loads(args.request)
            if request.get('confirmed') is not True: raise ValueError('Explicit confirmation required')
            result={'status':'submitted; completion unverified', 'result':str(asyncio.run(perform(request.get('action'),plan=request.get('routine') if request.get('action')=='routine' else request.get('plan'))))[:200]}
        else:
            result=load(STATE/'snapshot.json',{})
            if 'error' in result: result['robotError']=result.pop('error')
            result['authPresent']=(Path.home()/'.roborock').exists()
            if args.command=='bar':result={k:result.get(k) for k in ['at','name','battery','state','cleanWater','dirtyWater']}
        print(json.dumps(result))
    except Exception as error:
        print(json.dumps({'error':type(error).__name__+': '+str(error)[:240]}))
        raise SystemExit(1)
if __name__=='__main__':main()
