"""Strict device-setting requests; no I/O."""
def validate(plan):
    if not isinstance(plan,dict) or plan.get('reviewed') is not True:
        raise ValueError('Explicit setting review required')
    key,value=plan.get('setting'),plan.get('value')
    if key=='volume':
        if type(value) is not int or not 0<=value<=100: raise ValueError('Volume must be 0–100')
    elif key in ('dnd','child_lock'):
        if type(value) is not bool: raise ValueError('Expected a boolean')
    else: raise ValueError('Unknown setting')
    return key,value
