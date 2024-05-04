


from guitarcomposer.ui.widgets.note_picker import note_picker

from guitarcomposer.ui.widgets.glyphs.constants import *


note_selection = [
    {"text":WHOLE_NOTE, "tooltip":"whole note"},
    {"text":HALF_NOTE, "tooltip":"half note"},
    {"text":QUATER_NOTE, "tooltip":"quarter note"},
    {"text":EIGTH_NOTE, "tooltip":"eight note"},
    {"text":SIXTEENTH_NOTE, "tooltip":"sixteenth note"},
    {"text":THRITYSEC_NOTE, "tooltip":"thirty second note"},
    {"text":SIXTYFORTH_NOTE, "tooltip":"sixty forth note"},


    {"text":WHOLE_REST, "tooltip":"whole note rest"},
    {"text":HALF_REST, "tooltip":"half note rest"},
    {"text":QUATER_REST, "tooltip":"quarter note rest"},
    {"text":EIGHTH_REST, "tooltip":"eight note rest"},
    {"text":SIXTEENTH_REST, "tooltip":"sixteenth note rest"},
    {"text":THRITYSEC_REST, "tooltip":"thirty second note rest"},
    {"text":SIXTYFORTH_REST, "tooltip":"sixty forth note rest"}

]


class duration_control(note_picker):
    def __init__(self, on_selected):
        super().__init__(
            note_selection, 
            on_selected, 
            True, 
            title="NOTE/REST DURATION"
        )

