from .track_event import track_event

from guitarcomposer.common import dynamic
from guitarcomposer.common import durationtypes as dur

DEFAULT_DYNAMIC = dynamic.MF
DEFAULT_DOTTED = False
DEFAULT_DOUBLE_DOTTED = False
DEFAULT_TRIPLET = False
DEFAULT_QUINTUPLET = False


class track_note_event(track_event):
    def __init__(self, **args):
        # note -> [<midi code>, .... ]
        # if empty then this is a rest,
        # if more than one it is a chord.
        self.notes = []
        # None is simultaneuos or 'up' or 'down'
        self.stroke = None
        # 0.0 - 1.0 as the decimal percentage that
        # the stroke consumes the duration of the 
        # notes.
        self.stroke_duration = 0
        # variance of dynamic for each note
        self.stroke_dynamics = []
        
        self.duration = args.get("duration")
        self.dynamic = args.get("dynamic",DEFAULT_DYNAMIC)
        self.dotted = args.get("dotted",DEFAULT_DOTTED)
        self.double_dotted = \
            args.get("double_dotted", DEFAULT_DOUBLE_DOTTED)
        self.triplet = args.get("triplet", DEFAULT_TRIPLET)
        self.quintuplet = args.get("quintuplet",DEFAULT_QUINTUPLET)
        
        
