from typing import List, Tuple

from models.measure import TabEvent


class Note:
    DEFAULT_PITCH_RANGE = 2.0

    def __init__(self):
        self.midi_code : int | None = None
        self.velocity : int | None = None
        self.rest = False

        self.duration : float | None = None

        self.fret : int | None = None
        self.string : int | None = None
        self.accent = '#'

        self.is_playing = False

        # pitch range in semitones
        self.pitch_range : float = self.DEFAULT_PITCH_RANGE
        # self.pitch_changes = [(when,pitch_change),...]
        # when -> decimal fraction (0-1.0) of duration
        # pitch_change -> float decimal fraction of pitch range.
        self.pitch_changes : List[Tuple[float,float]] = []

    def set_duration(self, te: TabEvent, dur: float):
        if te.legato:
            self.duration = None # don't schedule a noteoff event
        elif te.staccato:
            self.duration = dur * 0.5 # ensure a rest encompasses 1/2 the duration
        else:
            self.duration = dur