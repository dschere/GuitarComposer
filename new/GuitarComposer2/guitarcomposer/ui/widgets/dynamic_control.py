
from guitarcomposer.common import dynamic as dyn
from .note_picker import note_picker


dynamic_selection = [
    {"text": "FFF", "tooltip": "fortississimo", "midi_value":dyn.FFF},
    {"text": "FF" , "tooltip": "fortissimo", "midi_value":dyn.FF},
    {"text": "F"  , "tooltip": "forte", "midi_value":dyn.F},

    {"text": "MF" , "tooltip": "mezzo-forte", "midi_value":dyn.MF},
    {"text": "MP" , "tooltip": "mezzo-piano", "midi_value":dyn.MP},

    {"text": "P"  , "tooltip": "piano", "midi_value":dyn.P},
    {"text": "PP" , "tooltip": "pianissimo", "midi_value":dyn.PP},
    {"text": "PPP", "tooltip": "pianississimo", "midi_value":dyn.PPP}    
]


class dynamic_control(note_picker):
    def __init__(self, on_selected):
        lookup = {}
        for ds in dynamic_selection:
            lookup[ds['text']] = ds['midi_value']
        super().__init__(
            dynamic_selection, 
            lambda text: on_selected(text, lookup[text]), 
            True, 
            max_buttons_per_column=4,
            size=48,
            hover_size=52,
            hover_font_size_change=False,
            title="DYNAMIC"
        )
