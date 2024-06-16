""" 
A track cursor saved the state of the current duration, dynamic
and staff meta info whlle editing.

So if I set the dynamic to forte I save the state for the
next note edit to have the same dynamic until changed.




"""

from .track_meta_event import track_meta_event
from .track_note_event import track_note_event

class track_cursor:
    def __init__(self, track):
        # holds the state of the last edited item for this 
        # track.
        self.track = track
        self.meta = track_meta_event()
        self.note = track_note_event()


