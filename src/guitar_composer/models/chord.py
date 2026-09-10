

from typing import List

from guitar_composer.models.note import Note


class Chord:
    """Represents a musical chord comprising multiple notes and strum direction attributes."""

    def __init__(self):
        """Initialize an empty Chord instance with default stroke and duration properties."""
        self.notes : List[Note] = []
        self.upstroke = False
        self.downstroke = False
        self.stroke_druation = 0
        self.chord_duration = 0

    