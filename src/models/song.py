

from typing import List
from models.track import Track


class Song:
    def __init__(self):
        # instrument name -> list of measures
        self.tracks : List[Track]  = []
        self.title = "noname"
        self.author = ""
        self.poly_rythm_tracks = False
        self.filename = ""
