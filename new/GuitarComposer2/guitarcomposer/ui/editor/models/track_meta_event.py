
from .track_event import track_event

DEFAULT_BPM = 120
DEFAULT_KEY = "C"
DEFAULT_TIMESIG = (4,4)
DEFAULT_LEGATO = False
DEFAULT_STACCATO = False


class track_meta_event(track_event):
    def __init__(self, **args):
        self.bpm = args.get("bpm", DEFAULT_BPM)
        self.key = args.get("key", DEFAULT_KEY)
        self.timesig = args.get("timesig", DEFAULT_TIMESIG)
        self.legato = args.get("legato", DEAFAUL_LEGATO)
        self.staccato = args.get("staccato", DEAFAUL_STACCATO)
        
        
