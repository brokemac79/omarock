"""Instance-local V1 decoded-grid tap; opaque protocol stays in vendor parser.

Private library hooks are feature-checked and failures leave normal maps usable.
No global monkey patch, device writes, metric area or coverage inference.
"""
from room_mask import decode


class GridTap:
    def __init__(self, delegate):
        self.delegate = delegate
        self.mask = None
        self.error = None

    def parse(self, raw_data, width, height, carpet_map, removed_map=None):
        # Vendor rendering remains authoritative and runs even if our tap rejects.
        self.mask = None
        self.error = None
        try:
            self.mask = decode(raw_data, width, height, removed_map)
        except (ValueError, TypeError):
            self.error = 'Unsupported vendor room grid'
        return self.delegate.parse(raw_data, width, height, carpet_map, removed_map)


def attach(parser):
    """Attach only to this fresh parser instance; unsupported versions fail closed."""
    inner = getattr(parser, '_map_parser', None)
    delegate = getattr(inner, '_image_parser', None)
    if delegate is None or not callable(getattr(delegate, 'parse', None)):
        return None
    tap = GridTap(delegate)
    inner._image_parser = tap
    return tap
