

DOWNSTROKE = 0
UPSTROKE = 1

class chord:
    def __init__(self):
        self.notes = []
        # decimal percentage of the chord duration, so 0.25
        # means that a chord that is made of quarter notes will
        # spend one sixteenth note playing each of the notes 
        # in order then the remaining 75% playing all. 
        self.stroke_speed = 0.25
        self.stroke_direction = DOWNSTROKE

