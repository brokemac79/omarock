"""Durable history and deduplicated local desktop alerts; never invent room coverage."""
import datetime as dt

def merge_history(old,new,clock=None):
    clock=clock if clock is not None else dt.datetime.now(dt.timezone.utc).timestamp()
    records={}
    for r in old+new:
        begin=r.get('begin')
        if type(begin) not in (int,float) or not clock-120*86400 <= begin <= clock+300: continue
        key=(begin,r.get('map_flag'))
        records[key]=dict(records.get(key,{}),**r)
    return sorted(records.values(),key=lambda r:r['begin'],reverse=True)[:2000]

def alerts(snapshot):
    result={}
    if snapshot.get('demo'): return result
    for key,name in [('cleanWater','Clean-water tank'),('dirtyWater','Dirty-water tank'),('dockError','Dock'),('robotError','Robot')]:
        value=snapshot.get(key)
        if value not in (None,False,0,'none','okay','ok','unknown','0'):
            result[key]=name+': '+str(value).replace('_',' ')
    for key,hours in snapshot.get('consumables',{}).items():
        if type(hours) in (int,float) and hours<=24:result['maintenance:'+key]=key.replace('_',' ')+': '+str(hours)+' usage hours remaining'
    return result

def notify(snapshot,previous,clock,send):
    active=alerts(snapshot);saved={}
    for key,value in active.items():
        before=previous.get(key,{})
        sent=before.get('sent',0)
        if before.get('message')!=value or not sent:
            if clock-before.get('attempt',0)>=300:
                ok=send('OmaRock',value)
                saved[key]={'message':value,'attempt':clock,'sent':clock if ok else 0}
                continue
        saved[key]={'message':value,'attempt':before.get('attempt',0),'sent':sent}
    return saved
