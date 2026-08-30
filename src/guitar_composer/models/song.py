

from typing import List
from guitar_composer.models.track import Track
import uuid


class Song:
    def __init__(self):
        # instrument name -> list of measures
        self.uuid = str(uuid.uuid4())
        self.tracks : List[Track]  = []
        self.title = "noname"
        self.author = ""
        self.poly_rythm_tracks = False
        self.filename = ""
        self.key = ""
