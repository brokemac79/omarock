"""Exact cell rectangles for zero-rotation V1 maps; unsupported frames fail closed.

No metric areas or cleaning coverage are inferred.
"""
def project(mask, config, left=0, top=0):
    import math
    if not mask or config.rotate != 0:
        return None
    width, height = mask['width'], mask['height']
    scale = config.scale
    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        return None
    trim = config.trim
    l, r = int(trim.left*width/100), int(trim.right*width/100)
    t, b = int(trim.top*height/100), int(trim.bottom*height/100)
    if min(l,r,t,b) < 0 or l+r >= width or t+b >= height:
        return None
    rooms = []
    for room in mask['rooms']:
        rects = []
        for y, start, end in room['spans']:
            start, end = max(start,l), min(end,width-r)
            if b <= y < height-t and start < end:
                rects.append([(start-l)*scale-left,
                              (height-t-y-1)*scale-top,
                              (end-start)*scale, scale])
        if rects:
            rooms.append({'id':room['id'], 'rects':rects})
    return {'coordinateFrame':'cropped-image-pixels', 'rooms':rooms,
            'coverage':'unverified', 'metricArea':None}
