"""Fail-closed dock-cycle review and capability checks. No I/O."""
ACTIONS={'wash':'is_washable','stop_wash':'is_washable','empty':'is_collectable','stop_empty':'is_collectable','dry':'is_dryable','stop_dry':'is_dryable'}
def capabilities(status):
    from roborock.device_features import RoborockDockFeatures
    dock=getattr(status,'dock_type',None)
    if dock is None: return {}
    features=RoborockDockFeatures.from_dock_type(dock,has_am=getattr(status,'has_am',None))
    return {key:getattr(features,field,False) is True for key,field in ACTIONS.items()}
def validate(plan,status,supported=None):
    if not isinstance(plan,dict) or plan.get('reviewed') is not True: raise ValueError('Explicit dock-cycle review required')
    action=plan.get('cycle')
    if action not in ACTIONS or not (supported if supported is not None else capabilities(status)).get(action): raise ValueError('Dock action unavailable')
    if not getattr(status,'is_battery_charging',False): raise ValueError('Robot must be confirmed charging at its dock')
    if status.in_cleaning or status.in_returning or status.error_code or status.dock_error_status: raise ValueError('Resolve busy state or robot/dock warnings first')
    if action in ('wash','empty','dry') and (getattr(status,'wash_status',None)!=0 or getattr(status,'dry_status',None)!=0): raise ValueError('Dock cycle active or status unknown')
    return action
