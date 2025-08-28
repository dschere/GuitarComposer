
WHOLE = 4.0
HALF = 2.0
QUARTER = 1.0
EIGHT = 0.5
SIXTEENTH = 0.25
THIRTYSECOND = 0.125
SIXTYFORTH = 0.0625
ONETWENTYEIGHT = 0.03125


# multipliers
DOTTED = 1.5
DOUBLE_DOTTED = 1.75
TRIPLET = 0.333

class state:
    def __init__(self, dur):
        self.dur = dur
        self.dotted = False
        self.double_dotted = False
        self.triplet = False 
        self.quintuplet = False  

lookup = [state(-1)] * 129


def create_states(n, dur):
    s = state(dur)
    lookup[n] = s 

    i = int(n * 1.5)
    if lookup[i].dur == -1: 
        s = state(dur)
        s.dotted = True 
        lookup[i] = s 

    i = int(n * 1.75)
    if lookup[i].dur == -1: 
        s = state(dur)
        s.double_dotted = True 
        lookup[i] = s

    i = int(n * 2/3.0)
    if lookup[i].dur == -1: 
        s = state(dur)
        s.triplet = True 
        lookup[i] = s

    i = int(n * 2/5.0)
    if lookup[i].dur == -1: 
        s = state(dur)
        s.quintuplet = True 
        lookup[i] = s


lookup[128] = state(WHOLE)

create_states(64, HALF)
create_states(32, QUARTER)
create_states(16, EIGHT)
create_states(8, SIXTEENTH)
create_states(4, THIRTYSECOND)
create_states(2, SIXTYFORTH)

for n in range(128,1,-1):
    if lookup[n].dur != -1:
        print(f"{n} {lookup[n].dur} {lookup[n].dotted} {lookup[n].double_dotted} {lookup[n].triplet}")


"""
loop once with no dots,triplets etc.
then keep looking trying dots and double dots
and return the nearest match if no exact match is found.
"""