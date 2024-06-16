"""
Represents a peice of music. 

* list of tracks
* meta information.
"""

from .track_cursor import track_cursor

        
class Score:
    def __init__(self):
        self.tracks = {}
        self.meta = {}
 
    def cursor(self, track_name):
        track = self.tracks[track_name]
        return track_cursor(track)
        

        
