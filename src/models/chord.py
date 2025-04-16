

from typing import List

from models.note import Note


class Chord:
    def __init__(self):
        self.notes : List[Note] = []
        self.upstroke = False
        self.downstroke = False
        self.stroke_druation = 0
        self.chord_duration = 0

    