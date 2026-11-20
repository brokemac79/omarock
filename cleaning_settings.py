"""Model-derived options and strictly reviewed cleaning preference changes."""
FIELDS={'suction':('fan_speed_mapping','fan_power','SET_CUSTOM_MODE'),'water':('water_mode_mapping','water_box_mode','SET_WATER_BOX_CUSTOM_MODE'),'mop_route':('mop_route_mapping','mop_mode','SET_MOP_MODE')}
def snapshot(status):
    result={}
    for key,(mapping,current,_) in FIELDS.items():
        try:
            value=getattr(status,current)
            options=getattr(status,mapping)
            if type(value) is not int or value not in options: continue
            result[key]={'value':value,'options':[{'value':k,'label':v} for k,v in options.items() if type(k) is int and isinstance(v,str)]}
        except (AttributeError,TypeError,ValueError): pass
    return result
def validate(plan,status):
    if not isinstance(plan,dict) or plan.get('reviewed') is not True: raise ValueError('Explicit preference review required')
    key,value=plan.get('setting'),plan.get('value')
    row=snapshot(status).get(key)
    if type(value) is not int or not row or value not in [o['value'] for o in row['options']]: raise ValueError('Preference unsupported or stale')
    return FIELDS[key][2],value
