

standard_tuning = ["E5","B4","G4","D4","A3","E3"]

from .note import note



class track:
    def __init__(self, **kwargs):
        self.instrument = None
        self.tuning = standard_tuning
        self.moments = []
        # normally this is the same for all tracks, but
        # having it here allows for polyrthym.
        self.timesig = (4,4)
        # if set to a list then the dynamic will follow that pattern
        self.beat_dynamic = None
        self.lagotto = True
        self.staccato = False
        
        for (k,v) in kwargs.items():
            setattr(self, k, v)

     
