


class track_event:
    def __init__(self):
        self.time_pos = None
        self.seq_pri = 0

class command(track_event):
    def __init__(self):
        super().__init__()

        self.lagato = False
        self.stacatto = False
        self.duration = 0
        self.seq_pri = 1
                    
class note(track_event):
    def __init__(self):
        super().__init__()
        self.duration = None
        self.midi_code = None
        self.g_string = None
        self.fret = None

        self.dynamic = None
        
        self.muted = False
        self.vibrato = None
        self.deadnote = False
        self.harmonic = None
        self.bend = None

class rest(track_event):
    def __init__(self):
        super().__init__()
        self.duration = None             
        
class chord(track_event):
    def __init__(self):
        super().__init__()

        self.notes = []
        self.stroke = "down"
        self.stroke_duration = None
        self.duration = None                     
