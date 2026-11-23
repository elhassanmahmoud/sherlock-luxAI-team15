import unittest
import numpy as np
from signalgrenze import bounds


class PublicBounds(unittest.TestCase):
    def test_seen_empty_fields_and_stacked_units(self):
        board=np.ones((24,24),bool)
        marks=np.zeros_like(board)
        marks[1,1:5]=True
        pos=np.zeros((2,16,2),int)
        active=np.zeros((2,16),bool)
        active[0,:2]=active[1,:3]=True
        pos[0,0]=pos[0,1]=[1,1]
        pos[1,0]=pos[1,1]=[1,2]
        pos[1,2]=[8,8]
        view=dict(sensor_mask=board,units_mask=active,units=dict(position=pos,energy=np.ones((2,16,1))))
        self.assertEqual(bounds(view,0,marks),(1,1))
        board[1,3:5]=False
        self.assertEqual(bounds(view,0,marks),(1,3))

    def test_an_unseen_fleet_has_only_sixteen_ships(self):
        empty=np.zeros((24,24),bool)
        view=dict(sensor_mask=empty,units_mask=np.zeros((2,16),bool),
                  units=dict(position=np.full((2,16,2),-1),energy=np.full((2,16,1),-1)))
        self.assertEqual(bounds(view,1,~empty),(0,16))


if __name__=="__main__":
    unittest.main()
