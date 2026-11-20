"""Bounded independent path captures; never inferred room or cleaning coverage."""
import copy
import hashlib
import json
import math

def merge(existing, floor, capture):
    rows=list(existing) if isinstance(existing,list) else []
    if type(floor) is not int or floor < 0 or not isinstance(capture,dict): return rows[-120:]
    paths=(capture.get('layers') or {}).get('path') or []
    valid=[]
    for line in paths:
        if line.get('kind') not in ('path','mop_path'): continue
        points=line.get('points') or []
        if not 2 <= len(points) <= 50000: continue
        if any(not isinstance(p,(list,tuple)) or len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in points): continue
        valid.append(copy.deepcopy(line))
    frame=capture.get('calibration')
    at=capture.get('mapAt')
    if not valid or not frame or not isinstance(at,str): return rows[-120:]
    # Captures retain their own frame: never join paths across crops or floors.
    payload={'floor':floor,'calibration':frame,'paths':valid}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    if any(r.get('digest')==digest for r in rows): return rows[-120:]
    rows.append(dict(payload,at=at,digest=digest,evidence='vendor path only; mode and room coverage unverified'))
    return rows[-120:]

def summarize(rows, floor):
    """Report independent vendor captures, never swept area or vacuum mode."""
    captures=[r for r in (rows if isinstance(rows,list) else [])
              if isinstance(r,dict) and type(r.get('floor')) is int and r['floor']==floor]
    counts={kind:sum(any(isinstance(p,dict) and p.get('kind')==kind
                        for p in (r.get('paths') if isinstance(r.get('paths'),list) else []))
                    for r in captures) for kind in ('path','mop_path')}
    stamps=[r['at'] for r in captures if isinstance(r.get('at'),str)]
    return {'captures':len(captures),'pathCaptures':counts['path'],
            'mopPathCaptures':counts['mop_path'],'latest':max(stamps) if stamps else None,
            'vacuumCoverage':'unverified','mopCoverage':'unverified'}
