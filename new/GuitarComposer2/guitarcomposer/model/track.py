
# string number -> midi code
standard_tuning = {
    1: 64,
    2: 59,
    3: 55,
    4: 50,
    5: 45,
    6: 40
}


from guitarcomposer.ui.widgets.glyphs.constants import *
from guitarcomposer.model.instrument import instrument


class track:
    
    def __init__(self, **kwargs):
        self.ins = instrument()
        self.tuning = standard_tuning
        self.events = []
        # normally this is the same for all tracks, but
        # having it here allows for polyrthym.
        self.timesig = (4,4)
        # if set to a list then the dynamic will follow that pattern
        self.beat_dynamic = None
        self.lagatto = True
        self.staccato = False
        self.cleff = TREBLE_CLEFF
        self.id = ""
        self.measures = []


        for (k,v) in kwargs.items():
            setattr(self, k, v)

     
