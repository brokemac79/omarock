import unittest
from types import SimpleNamespace as NS
from room_mask import decode
from mask_projection import project

def config(**kw):
    return NS(rotate=kw.get('rotate',0), scale=kw.get('scale',4),
              trim=NS(left=kw.get('left',0),right=0,top=0,bottom=kw.get('bottom',0)))

class ProjectionTests(unittest.TestCase):
    def test_bottom_up_scale_and_crop(self):
        mask=decode(bytes([135,135,0,0]),2,2)
        self.assertEqual(project(mask,config(),1,2)['rooms'][0]['rects'],[[-1,2,8,4]])
    def test_nonrectangular_shape_preserved(self):
        mask=decode(bytes([135,0,135,135]),2,2)
        self.assertEqual(project(mask,config(scale=1))['rooms'][0]['rects'],
                         [[0,1,1,1],[0,0,2,1]])
    def test_trim_excludes_cells(self):
        mask=decode(bytes([135]*16),4,4)
        rects=project(mask,config(left=25,bottom=25,scale=1))['rooms'][0]['rects']
        self.assertEqual(rects,[[0,2,3,1],[0,1,3,1],[0,0,3,1]])
    def test_unsupported_frames_fail_closed(self):
        mask=decode(bytes([135]),1,1)
        for c in [config(rotate=90),config(scale=0),config(scale=float('nan')),config(left=100)]:
            self.assertIsNone(project(mask,c))
        self.assertIsNone(project(None,config()))
