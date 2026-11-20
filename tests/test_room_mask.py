import unittest
import room_mask


class RoomMask(unittest.TestCase):
    def test_exact_cells_not_bounds(self):
        result = room_mask.decode(bytes([135, 0, 135, 135, 135, 0]), 3, 2)
        self.assertEqual(result["rooms"], [{"id": 16, "spans": [[0, 0, 1], [0, 2, 3], [1, 0, 2]], "cellCount": 4}])
        self.assertIsNone(result["metricArea"])
        self.assertEqual(result["coverage"], "unverified")

    def test_special_pixels_not_rooms(self):
        self.assertEqual(room_mask.decode(bytes([0, 1, 7, 255, 128, 129]), 3, 2)["rooms"], [])

    def test_removed_cells_split_spans(self):
        r = room_mask.decode(bytes([135]*3), 3, 1, [1])
        self.assertEqual(r["rooms"][0]["spans"], [[0, 0, 1], [0, 2, 3]])

    def test_rooms_separate(self):
        r = room_mask.decode(bytes([143, 135]), 2, 1)
        self.assertEqual([x["id"] for x in r["rooms"]], [16, 17])

    def test_reject_invalid_dimensions(self):
        for w,h in [(True, 1), (0, 1), (1, -1), (1.0, 1), (4000001, 1)]:
            with self.assertRaises(ValueError): room_mask.decode(b"", w, h)

    def test_reject_wrong_length_and_type(self):
        for raw in [b"", b"xx", "x"]:
            with self.assertRaises(ValueError): room_mask.decode(raw, 1, 1)
