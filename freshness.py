"""Room-scoped activity evidence, not inferred mode or surface coverage."""
import math
import time

def summarize(maps, history, clock=None):
    clock=time.time() if clock is None else clock
    result={}
    for floor in maps:
        fid=floor.get('id')
        if type(fid) is not int: continue
        rooms={}
        for room in floor.get('rooms',[]):
            rid=room.get('id')
            if type(rid) is not int: continue
            times=[]
            for record in history:
                if not isinstance(record,dict): continue
                if type(record.get('map_flag')) is not int or record['map_flag']!=fid: continue
                ids=record.get('area_ids')
                if not isinstance(ids,list) or not any(type(i) is int and i==rid for i in ids): continue
                # Only a completed record with an explicit room id is activity evidence.
                complete=record.get('complete')
                if type(complete) not in (bool,int) or complete not in (True,1): continue
                stamp=record.get('end')
                if type(stamp) not in (int,float) or not math.isfinite(stamp) or not 0<stamp<=clock: continue
                times.append(stamp)
            last=max(times) if times else None
            rooms[str(rid)]={'last':last,'ageDays':int((clock-last)//86400) if last is not None else None,
                            'evidenceRuns':len(times),'coverage':'unverified','mode':'unknown'}
        result[str(fid)]=rooms
    return result
