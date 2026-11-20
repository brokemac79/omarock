"""Vendor usage-life estimates and fail-closed reset review."""
import math
FIELDS = {"main_brush":"main_brush_work_time", "side_brush":"side_brush_work_time", "filter":"filter_work_time", "sensor":"sensor_dirty_time"}

def percentage(seconds, lifetime):
    if type(seconds) not in (int,float) or type(lifetime) not in (int,float) or not math.isfinite(seconds) or not math.isfinite(lifetime) or lifetime<=0:
        return None
    return round(max(0,min(100,seconds/lifetime*100)))

def validate_reset(plan):
    if not isinstance(plan,dict) or plan.get("afterReplacement") is not True:
        raise ValueError("Confirm replacement or sensor cleaning before resetting usage")
    key=plan.get("consumable")
    if key not in FIELDS: raise ValueError("Unknown consumable")
    return key
