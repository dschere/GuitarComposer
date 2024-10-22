
class track:
    def __init__(self):
        self.instrument_name = None
        self.channel = None
        self.tuning = [
            "E4",
            "B3",
            "G3",
            "D3",
            "A2",
            "E2"
        ]


class guitar_track(track):
    def __init__(self):
        super().__init__()  
                  
        # map instrument name to channel
        self.instr_map = {}
        # map of string number to 
        # velecoty multiple and instrument
        self.string_map = []

class acoustic_guitar(guitar_track):
    def __init__(self):
        super().__init__()            

        

