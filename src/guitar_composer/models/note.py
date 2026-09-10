from typing import List, Tuple

from guitar_composer.models.measure import TabEvent


class Note:
    DEFAULT_PITCH_RANGE = 2.0

    def __str__(self):
        """Return a string representation of the note including MIDI code, velocity, and duration."""
        return f"note midi_code={self.midi_codes} velocity={self.velocity} duration={self.duration}"

    def __init__(self, **kwargs):
        """Initialize a Note instance with MIDI, pitch, and playback properties.

        Args:
            **kwargs: Optional attributes including midi_code, velocity, rest, and duration.
        """
        self.midi_codes : int | None = kwargs.get('midi_code')
        self.velocity : int | None = kwargs.get('velocity')
        self.rest = kwargs.get('rest', False)

        self.duration : float | None = kwargs.get('duration')

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
        """Set note duration based on articulation settings (legato or staccato) from a TabEvent.

        Args:
            te: TabEvent providing legato and staccato articulation flags.
            dur: Nominal duration in seconds.
        """
        if te.legato:
            self.duration = None # don't schedule a noteoff event
        elif te.staccato:
            self.duration = dur * 0.5 # ensure a rest encompasses 1/2 the duration
        else:
            self.duration = dur