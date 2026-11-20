"""Observed path-age cells. No cleaning/swath/mode/completion inference."""
import datetime as dt
import math

def affine(calibration,source='map',target='vacuum'):
    if not isinstance(calibration,list) or len(calibration)!=3: raise ValueError('Three calibration points required')
    a,b,c=calibration
    def xy(p,k):
        q=p[k];x,y=q['x'],q['y']
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (x,y)): raise ValueError('Invalid calibration')
        return x,y
    ax,ay=xy(a,source);bx,by=xy(b,source);cx,cy=xy(c,source)
    u,v=bx-ax,by-ay;w,z=cx-ax,cy-ay;det=u*z-v*w
    if abs(det)<1e-9: raise ValueError('Degenerate calibration')
    ta,tb,tc=xy(a,target),xy(b,target),xy(c,target)
    def convert(p):
        x,y=p
        if any(type(n) not in (int,float) or not math.isfinite(n) for n in p): raise ValueError('Invalid path point')
        s=((x-ax)*z-(y-ay)*w)/det;t=(u*(y-ay)-v*(x-ax))/det
        return [ta[0]+s*(tb[0]-ta[0])+t*(tc[0]-ta[0]),ta[1]+s*(tb[1]-ta[1])+t*(tc[1]-ta[1])]
    return convert

def build(captures,floor,frame,clock=None):
    clock=clock if clock is not None else dt.datetime.now(dt.timezone.utc).timestamp()
    empty={'cells':[],'available':False,'truncated':False,'meaning':'Observed generic/mop path age only; no swept-area, vacuum-mode or completed-clean proof'}
    try:project=affine(frame,'vacuum','map')
    except (ValueError,KeyError,TypeError):return empty
    cells={};budget=150000
    for capture in captures if isinstance(captures,list) else []:
        if capture.get('floor')!=floor or type(capture.get('floor')) is not int:continue
        try:
            stamp=dt.datetime.fromisoformat(capture['at']).timestamp()
            if not 0<stamp<=clock or clock-stamp>120*86400:continue
            convert=affine(capture['calibration'])
            for path in capture.get('paths',[]):
                if path.get('kind') not in ('path','mop_path'):continue
                pts=path.get('points',[])
                for start,end in zip(pts,pts[1:]):
                    a,b=convert(start),convert(end)
                    # Sample centreline only; never assume robot cleaning width.
                    count=max(1,math.ceil(math.dist(a,b)/25))
                    if count>4000:continue # discontinuity/teleport, not a swept line
                    for i in range(count+1):
                        budget-=1
                        if budget<0:break
                        x=a[0]+(b[0]-a[0])*i/count;y=a[1]+(b[1]-a[1])*i/count
                        key=(math.floor(x/50),math.floor(y/50),path['kind'])
                        if stamp>cells.get(key,0):cells[key]=stamp
                    if budget<0:break
                if budget<0:break
        except (ValueError,KeyError,TypeError,OverflowError):continue
        if budget<0:break
    rendered=[]
    for (x,y,kind),stamp in cells.items():
        corners=[project([x*50,y*50]),project([(x+1)*50,y*50]),project([(x+1)*50,(y+1)*50]),project([x*50,(y+1)*50])]
        age=int((clock-stamp)//86400)
        rendered.append({'points':corners,'at':stamp,'ageDays':age,'kind':kind,'color':'#77cc99' if age<2 else '#efbb66' if age<7 else '#ee8888'})
    return dict(empty,cells=rendered,available=bool(rendered),truncated=budget<0)
