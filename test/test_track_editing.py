#!/usr/bin/env python

import unittest

from models.track import * 
from music.durationtypes import *

class TestTrackMoments(unittest.TestCase):
    def test_2_compute_measure_beats(self):
        track = Track()
        seq = track.getSequence() 

        staff_e = StaffEvent()
        measure_e = MeasureEvent()

        # 3 quater notes
        q1 = TabEvent(len(track.tuning))
        q1.duration = QUARTER

        q2 = TabEvent(len(track.tuning))
        q2.duration = QUARTER

        q3 = TabEvent(len(track.tuning))
        q3.duration = QUARTER

        seq.add(0, staff_e)
        seq.add(0, measure_e)
        seq.add(0, q1)
        seq.add(1, q2)
        seq.add(2, q3)

        r = staff_e.compute_timespec()

        (moment,_) = seq.search(2, seq.BACKWARD, seq.MEASURE_EVENT)
        assert(moment == 0)
        # compute total beats 
        beats = 0.0
        for m in (0,1,2):
            te = seq.getEvent(m,seq.TAB_EVENT)
            assert(te)
            beats += te.beats(r.beat_duration) 
        assert(beats == 3.0)

        duration_left = (r.beats_per_measure*r.beat_duration) - beats 
        assert(duration_left == 1.0)

        assert(seq.getActiveStaff(2))

    def test_1_primitives(self):
        staff_e = StaffEvent()
        r = staff_e.compute_timespec()
        assert(r.beats_per_measure == 4)
        assert(r.beat_duration == QUARTER)    

        staff_e.signature = "6/8"
        r = staff_e.compute_timespec()
        assert(r.beats_per_measure == 6)
        assert(r.beat_duration == EIGHTH)   

        dt = DurationTable
        
        expected = (1.5, True, False, False, False,1.0)
        t = 1.5
        actual = dt.nearest(t)
        assert(actual == expected)

        print(dt.nearest(2 * 0.66666))

        q1 = TabEvent(6)
        q1.duration = QUARTER

        track = Track()
        seq = track.getSequence() 

        seq.add(0, staff_e) 
        seq.add(0, q1)
        staff = seq.getActiveStaff(0)
        assert(staff)




if __name__ == '__main__':
    unittest.main()