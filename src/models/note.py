class Note:
    DEFAULT_PITCH_RANGE = 2

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
        self.pitch_range = self.DEFAULT_PITCH_RANGE
        # self.pitch_changes = [(when,pitch_change),...]
        # when -> decimal fraction (0-1.0) of duration
        # pitch_change -> float decimal fraction of pitch range.
        self.pitch_changes = []
