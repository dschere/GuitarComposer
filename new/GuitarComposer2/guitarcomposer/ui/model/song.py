

class song:
    def __init__(self):
        self.title = ""
        self.author = ""
        self.alblum = ""
        # name -> track class instance
        self.tracks = {}
        # sharps, flats. C major has none
        self.key = []
        # tempo in beats per minute 
        self.bpm = 120
        
