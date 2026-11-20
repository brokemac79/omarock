import unittest
from types import SimpleNamespace
from mask_capture import GridTap, attach


class Delegate:
    def __init__(self):
        self.calls = []
    def parse(self, *args):
        self.calls.append(args)
        return 'vendor-result'


class CaptureTests(unittest.TestCase):
    def test_valid_capture_preserves_rendering(self):
        delegate = Delegate()
        tap = GridTap(delegate)
        self.assertEqual(tap.parse(bytes([135, 135]), 2, 1, None), 'vendor-result')
        self.assertEqual(tap.mask['rooms'][0]['cellCount'], 2)
        self.assertEqual(len(delegate.calls), 1)

    def test_removed_cells(self):
        tap = GridTap(Delegate())
        tap.parse(bytes([135, 135]), 2, 1, None, {0})
        self.assertEqual(tap.mask['rooms'][0]['spans'], [[0, 1, 2]])

    def test_invalid_grid_still_delegates(self):
        tap = GridTap(Delegate())
        self.assertEqual(tap.parse(b'', 2, 1, None), 'vendor-result')
        self.assertIsNone(tap.mask)
        self.assertIsNotNone(tap.error)

    def test_capture_does_not_reuse_stale_mask(self):
        tap = GridTap(Delegate())
        tap.parse(bytes([135]), 1, 1, None)
        tap.parse(b'', 1, 1, None)
        self.assertIsNone(tap.mask)

    def test_attach_is_instance_local(self):
        delegate = Delegate()
        first = SimpleNamespace(_map_parser=SimpleNamespace(_image_parser=delegate))
        second = SimpleNamespace(_map_parser=SimpleNamespace(_image_parser=delegate))
        tap = attach(first)
        self.assertIs(first._map_parser._image_parser, tap)
        self.assertIs(second._map_parser._image_parser, delegate)

    def test_unknown_library_fails_closed(self):
        self.assertIsNone(attach(object()))
