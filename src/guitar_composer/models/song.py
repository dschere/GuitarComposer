

from typing import List
from guitar_composer.models.track import Track
import uuid


class Song:
    """Represents a musical composition comprising multiple tracks, metadata, and arrangement settings."""

    def __init__(self):
        """Initialize a new Song instance with a unique identifier and default attributes."""
        # instrument name -> list of measures
        self.uuid = str(uuid.uuid4())
        self.tracks : List[Track]  = []
        self.title = "noname"
        self.author = ""
        self.poly_rythm_tracks = False
        self.filename = ""
        self.key = ""
