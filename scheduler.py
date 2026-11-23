"""Desktop weekly scheduler: local time, at-most-once dispatch, no missed-job catch-up."""
import datetime as dt
import re
from zoneinfo import ZoneInfo

def validate(request,maps,controls=False):
    import planner
    p=planner.validate(dict(request,days=0),maps)
    hour=request.get('hour');minute=request.get('minute');weekdays=request.get('weekdays')
    if type(hour) is not int or not 0<=hour<24 or type(minute) is not int or not 0<=minute<60: raise ValueError('Invalid time')
    if not isinstance(weekdays,list) or not weekdays or any(type(d) is not int or not 0<=d<=6 for d in weekdays): raise ValueError('Choose weekdays')
    enabled=request.get('enabled') is True
    if enabled and (not controls or request.get('confirmed') is not True): raise ValueError('Automatic control locked: supervised commissioning and explicit confirmation required')
    return {k:p[k] for k in ('floor','room','mode')}|{'hour':hour,'minute':minute,'weekdays':sorted(set(weekdays)),'timezone':'Europe/London','enabled':enabled}

def valid_target(target):
    return isinstance(target, str) and re.fullmatch(r'v1:[0-9a-f]{64}', target) is not None


def require_target(expected, actual):
    if not valid_target(expected) or expected != actual:
        raise ValueError('Schedule target changed or is unconfirmed; refresh and recreate the schedule')


def slot(schedule,clock):
    local=clock.astimezone(ZoneInfo(schedule['timezone']))
    if not schedule.get('enabled') or local.weekday() not in schedule['weekdays']: return None
    if (local.hour,local.minute)!=(schedule['hour'],schedule['minute']): return None
    # Same date/time key in both autumn DST folds; never runs twice.
    return local.strftime('%Y-%m-%dT%H:%M')

async def tick(schedules,journal,clock,dispatch,persist):
    outcomes=[]
    for ident,s in schedules.items():
        due=slot(s,clock)
        token=ident+':'+str(due)
        if not due or token in journal: continue
        # Persist before command. Timeout/crash remains uncertain, never auto-retried.
        journal[token]={'status':'reserved; outcome unknown','at':clock.isoformat()};persist(journal)
        try:
            await dispatch(s)
            journal[token]['status']='submitted; completion unverified'
        except Exception as error:
            journal[token]['status']='skipped or uncertain: '+str(error)[:180]
        persist(journal);outcomes.append(journal[token])
    return outcomes
