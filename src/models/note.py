class Note:
    def __init__(self):
        self.midi_code = None
        self.velocity = None
        self.rest = False

        self.duration = None

        self.fret = None
        self.string = None
        self.accent = '#'

        self.is_playing = False
