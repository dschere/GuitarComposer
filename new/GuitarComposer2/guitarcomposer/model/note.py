


class note:
    def __init__(self):
        # None -> rest otherwise a number
        self.midi_code = None
        self.beat = None # filled in by the measure model
        
        # in beats so quarter in 1, sixteenth os 0.25 etc.
        self.duration = None
        
        # for presentation puposes
        self.dotted = False
        self.triplet = False
        self.quintuplet = False
        
        self.muted = False
        self.dead = False

        # 1-127 soft to loud 
        self.dynamic = 64

        self.harmonic = None
        self.vibrato = False 
        # decimal percentage of n.duration -> pitch bend in steps
        self.bend = None

        self.lagato = False
        self.stacatto = False