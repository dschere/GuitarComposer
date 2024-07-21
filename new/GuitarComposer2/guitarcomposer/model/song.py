from collections import OrderedDict
import copy

class undo_redo_activity:
    def __init__(self):
        self.undo_redo_buffer = []
        self.undo_redo_bufpos = 0
    


class song:
    
    def __init__(self):
        self.title = "noname"
        self.author = ""
        self.alblum = ""
        
        self.ur_activity = undo_redo_activity()
        
        # name -> track class instance
        self.tracks = OrderedDict()

        # tempo in beats per minute 
        self.bpm = 120

        # key name and sharp/flat notes that represent this
        # key on the staff
        self.key = "C"
        
    def encode(self):
        r = copy.deepcopy(self)
        r.ur_activity = undo_redo_activity()
        return r
        
            
        
