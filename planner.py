"""Local recurring cleaning plans. No robot commands or guessed room coverage."""
import datetime as dt

MODES=('vacuum','mop')
def validate(request,maps):
    if not isinstance(request,dict): raise ValueError('Invalid plan')
    floor=request.get('floor');room=request.get('room');mode=request.get('mode');days=request.get('days')
    match=next((m for m in maps if m['id']==floor),None)
    if type(floor) is not int or not match: raise ValueError('Unknown floor')
    if room is not None and (type(room) is not int or room not in [r['id'] for r in match.get('rooms',[])]): raise ValueError('Unknown room')
    if mode not in MODES: raise ValueError('Invalid mode')
    if type(days) is not int or not 0<=days<=30: raise ValueError('Interval must be 0–30 days')
    return {'floor':floor,'room':room,'mode':mode,'days':days}

def key(floor,room,mode): return f'{floor}:{room}:{mode}'

def timeline(maps,history,plans,clock=None):
    clock=clock or dt.datetime.now(dt.timezone.utc).timestamp()
    rows=[]
    for floor in maps:
        for room in [None]+floor.get('rooms',[]):
            rid=room['id'] if room else None
            lanes=[]
            for mode in MODES:
                plan=plans.get(key(floor['id'],rid,mode),{})
                # Record clean_type is a scope/type field, not a reliable vacuum/mop mode.
                # Keep imported evidence visible separately, never manufacture mode attribution.
                evidence=[r for r in history if r.get('map_flag')==floor['id'] and (rid is None or rid in (r.get('area_ids') or []))]
                days=plan.get('days',0)
                anchor=plan.get('anchor',clock)
                due=anchor+days*86400 if days else None
                lanes.append({'mode':mode,'days':days,'due':due,'last':None,'evidenceRuns':len(evidence),'status':'overdue' if due and due<clock else 'planned' if due else 'not scheduled'})
            rows.append({'floor':floor['id'],'room':rid,'name':room['name'] if room else floor['name']+' · whole floor','floorName':floor['name'],'lanes':lanes})
    return rows
