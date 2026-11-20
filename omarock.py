#!/usr/bin/env python3
"""OmaRock: loopback-only Roborock dashboard and Omarchy bar companion."""
import argparse
import asyncio
import base64
import datetime as dt
import json
import math
import os
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
                'activeFloor':s.current_map,'error':enum_name(s.error_code),'dockError':enum_name(s.dock_error_status),
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
        old=load(STATE/'snapshot.json',{})
        if include_map or old.get('activeFloor') != result['activeFloor'] or not old.get('mapImage'):
            try:
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
            except Exception: errors.append('Map unavailable')
        elif old.get('mapImage'):
            result['mapImage']=old['mapImage'];result['calibration']=old.get('calibration');result['mapAt']=old.get('mapAt',old.get('at'))
        if include_map and 'mapImage' in result: result['mapAt']=result['at']
        result['warnings']=errors
        return result
    async def execute(self, action, plan=None):
        if self.config.get('allow_control') is not True: raise ValueError('Control locked. Explicitly enable allow_control in your private config after supervised testing')
        await self.v.status.refresh()
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
        return await (robot.snapshot(**kwargs) if operation=='snapshot' else robot.execute(operation,**kwargs))
    finally: await robot.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['snapshot','cached','bar','action'])
    parser.add_argument('--request',default='{}')
    args=parser.parse_args()
    private_dir(STATE);private_dir(CONFIG)
    try:
        if args.command=='snapshot':
            result=asyncio.run(perform('snapshot',include_map=True))
            save(STATE/'snapshot.json',result)
        elif args.command=='action':
            request=json.loads(args.request)
            if request.get('confirmed') is not True: raise ValueError('Explicit confirmation required')
            result={'status':'submitted; completion unverified', 'result':str(asyncio.run(perform(request.get('action'),plan=request.get('plan'))))[:200]}
        else:
            result=load(STATE/'snapshot.json',{})
            result['authPresent']=(Path.home()/'.roborock').exists()
            if args.command=='bar':result={k:result.get(k) for k in ['at','name','battery','state','cleanWater','dirtyWater']}
        print(json.dumps(result))
    except Exception as error:
        print(json.dumps({'error':type(error).__name__+': '+str(error)[:240]}))
        raise SystemExit(1)
if __name__=='__main__':main()
