


class note_duration_controller:
    """
    Handle events from the view.note_duration_controls
    """
    
    def __init__(self):
        self.current_note = None
        self.dynamic = None
    
    def note_selected(self, selected):
        self.current_note = selected
        print("note_selected -> (%s)" % selected)
    
    def dynamic_selected(self, dyn_text, dyn_value):
        self.dynamic = dyn_value
        print(f"duration_selected -> ({dyn_text},{dyn_value})" )    
