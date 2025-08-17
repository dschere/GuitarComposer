import unittest

from models.track import Track
from models.measure import Measure, TimeSig, TabEvent
from music.durationtypes import *

class TestTrackModel(unittest.TestCase):
    def test_1_creation(self):
        t = Track()
        (te, m) = t.current_moment()
        assert(m.timesig)
        assert(m.timesig.beat_note_id == 4)
        assert(m.timesig.beats_per_measure == 4)
        assert(len(m.tab_events) == 4)
        assert(m.staff_changes)

    def test_2_append_measure(self):
        t = Track()
        m = t.blank_measure(measure_number=2)
        assert(m.measure_number == 2)
        t.measures.append(m)

    def test_3_navigation(self):
        t = Track()
        t.measures.append( t.blank_measure(measure_number=2) )
        t.measures.append( t.blank_measure(measure_number=3) )
        t.measures.append( t.blank_measure(measure_number=4) )
        t.set_moment(0,0)
        (tab_event, measure) = t.current_moment()
        assert(measure.measure_number == 1)
        assert(tab_event)
        # calling next moment 4 times should take us to the next measure
        for _ in range(4):
            t.next_moment()
        (tab_event, measure) = t.current_moment()
        assert(measure.measure_number == 2)
        assert(not measure.staff_changes)
        (_, m) = t.prev_moment()
        assert(m)
        assert(m.measure_number == 1)
        for _ in range(4):
            t.prev_moment()
        (tab_e, m) = t.prev_moment()
        assert(not tab_e)

        (tab_e, m) = t.next_moment()
        assert(tab_e)

        t.set_moment(0,0)
        for _ in range(16):
            t.next_moment()
        
        (tab_e,m) = t.next_moment()
        assert(not tab_e)
        




if __name__ == '__main__':
    unittest.main()

