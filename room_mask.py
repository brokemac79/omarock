"""Decode V1 vendor image bytes, never rendered colours or room bounding boxes.

Coordinates are untrimmed bottom-up vendor grid cells, not calibrated UI pixels.
This bounded decoder is preparation for a future capture adapter; it does not
claim observed coverage, metric area, or a usable floorplan.
"""
MAX_CELLS = 4_000_000


def decode(raw, width, height, removed=()):
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("Invalid grid dimensions")
    if width * height > MAX_CELLS:
        raise ValueError("Grid exceeds safety limit")
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != width * height:
        raise ValueError("Grid byte count mismatch")
    removed = set(removed or ())
    rows = {}
    for y in range(height):
        x = 0
        while x < width:
            idx = y * width + x
            value = raw[idx]
            room = value >> 3 if value not in (0, 1, 7, 255) and value & 7 == 7 and idx not in removed else None
            if room is None:
                x += 1
                continue
            start = x
            x += 1
            while x < width and raw[y * width + x] == value and y * width + x not in removed:
                x += 1
            rows.setdefault(room, []).append([y, start, x])
    return {"width": width, "height": height, "coordinateFrame": "vendor-bottom-up-grid",
            "rooms": [{"id": room, "spans": spans, "cellCount": sum(b-a for _, a, b in spans)}
                      for room, spans in sorted(rows.items())],
            "coverage": "unverified", "metricArea": None}
