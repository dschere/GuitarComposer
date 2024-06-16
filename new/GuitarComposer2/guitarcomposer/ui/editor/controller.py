


from guitarcomposer.ui.widgets.glyphs.constants import *
from guitarcomposer.ui.editor.view.editor_view import editor_view 



class track_controller:
    def __init__(self):
        # track model
        self.trak = None
        
        self.duration = QUARTER_NOTE
        self.dynamic = "MF"
        self.dotted = False
         

class editor_controller:
    def __init__(self):
        self.editor_view = editor_view
        self.track_list = []
        self.active_track = None
    
    def dynamic_event(self, text, midi_value):
        pass 
        
    def key_press(self, key):
        pass
        
    def key_release(self, key):
        pass        
        
    def duaration_event(self, note):
        pass   
        
    def subbeat_duration_event(self, note):
        pass
