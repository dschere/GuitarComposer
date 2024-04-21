from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *
from guitarcomposer.common import durationtypes as DT
from guitarcomposer.ui.theme import getTheme


per_octave_names = ['C', 'C#/Db', 'D', 'D#/Eb', 'E',
                    'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
accent_table = [False, True, False, True, False,
                False, True, False, True, False, True, False]

# generate two tables depending if we are used sharps or flats.
# this lookup table precomputes the number of pixels (in line_spacings)
# the note shall be rendered. Note an A# and Gb are the same note but
# drawn on a different y position on the staff, the values are computed
# from the G5 note which is the y_start position on the first line of
# the staff.


def generate_step_tables():
    sharp_step_table, flat_step_table = {}, {}

    # from C -> B count the y offset changes
    sharp_seq = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
    flat_seq = [0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6]

    midi_g5 = 91
    midi_g5_octave_offset = (7 * (int(midi_g5 / 12) - 2))
    sharp_offset = midi_g5_octave_offset + sharp_seq[midi_g5 % 12]
    flat_offset = midi_g5_octave_offset + flat_seq[midi_g5 % 12]

    for midi in range(24, 128):
        octave = int(midi / 12) - 2
        n_s = sharp_seq[midi % 12] + (7 * octave)
        n_f = flat_seq[midi % 12] + (7 * octave)

        sharp_step_table[midi] = sharp_offset - n_s
        flat_step_table[midi] = flat_offset - n_f

    return sharp_step_table, flat_step_table


sharp_step_table, flat_step_table = generate_step_tables()


class _note_renderer:
    def get_note_head_text(self, dtype):
        return {
            DT.WHOLE: VOID_NOTEHEAD,
            DT.HALF: VOID_NOTEHEAD
        }.get(dtype, BLACK_NOTEHEAD)

    def get_tail_note_text(self, dtype):
        return {
            DT.WHOLE: WHOLE_NOTE,
            DT.HALF: HALF_NOTE,
            DT.QUARTER: QUATER_NOTE,
            DT.EIGHT: EIGHT_NOTE,
            DT.SIXTEENTH: SIXTEENTH_NOTE,
            DT.THIRTYSECOND: THRITYSEC_NOTE,
            DT.SIXTYFORTH: SIXTYFORTH_NOTE
        }[dtype]

    def get_y_coord(self, midi_code, conf, accent):
        global sharp_step_table, flat_step_table

        line_spacing = conf.line_spacing
        y_start = conf.y_start - 10
        inc = line_spacing/2

        if accent == SHARP_SIGN:
            return int(y_start + (sharp_step_table[midi_code] * inc))
        else:
            return int(y_start + (flat_step_table[midi_code] * inc))

            
    def draw_note(self, painter, conf, midi_code, accent, dtype):    
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in 
        # different staff positions depending on which it is.    
        line_spacing = conf.line_spacing
        accent_spacing = conf.accent_spacing

        y = self.get_y_coord(midi_code, conf, accent)
        # do we need to render a # or b infront of the note?
        if accent_table[midi_code % 12]:

            size = conf.line_spacing
            font = QtGui.QFont("DejaVu Sans", int(size ))
            painter.setFont(font)

            # draw a sharp or flat sign next to the note head
            painter.drawText(0, y+3, accent)

            size = conf.line_spacing
            font = QtGui.QFont("DejaVu Sans", int(size * 1.5))
            painter.setFont(font)

        text = self.get_tail_note_text(dtype)
        painter.drawText(accent_spacing, y, text)
        
    def draw_notehead(self, painter, conf, midi_code, accent, dtype):    
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in 
        # different staff positions depending on which it is.    
        line_spacing = conf.line_spacing
        accent_spacing = conf.accent_spacing

        y = self.get_y_coord(midi_code, conf, accent)
        text = self.get_note_head_text(dtype)
        painter.drawText(accent_spacing, y, text)
        

class _chord_renderer:
    """
    Helper object used to draw a chord, in the case of a note 
    there are already key codes to draw the various notes, but 
    in the case of a chord we have to create it using a combination
    of overlayed text.

                   | <- tail ... positioned at the highest note.
                   | <- stem  
                   | 
       +-----------+ 
       | note head |
       +-----------+

    This can be implemented at a note with a flag indicating the
    duration, then the second third ... last notes are just the note 
    head of the first note. Then a stem line is drawn from last to 
    first. 
    """

    def draw(self, painter, conf, midi_codes, accent, dtype):
        assert len(midi_codes) > 0
        
        # arrange midi codes highest to lowest
        if len(midi_codes) > 1:
            midi_codes.sort()
            midi_codes.reverse()
        
        note_renderer = _note_renderer()
        midi_code = midi_codes[0]
        note_renderer.draw_note(\
            painter, conf, midi_code, accent, dtype )
        
        for midi_code in midi_codes[1:]:
            note_renderer.draw_notehead(\
                painter, conf, midi_code, accent, dtype)    

        if len(midi_codes) > 1 and dtype not in (DT.WHOLE,DT.HALF): 
            # configure a 2 pixel wide verticle line
            painter.setPen(QtGui.QPen(Qt.GlobalColor.black, 2))
            
            # draw a line connecting the notes is dtype is not
            # a whole or half note.
            line_spacing = conf.line_spacing
            accent_spacing = conf.accent_spacing
            
            low_y = note_renderer.get_y_coord(\
                midi_codes[-1], conf, accent)
            high_y = note_renderer.get_y_coord(\
                midi_codes[0], conf, accent)

            # x = the right side of the note head.
            stem_x = accent_spacing + int(line_spacing/2) + 1
            notehead_offset = int(line_spacing/7)
            painter.drawLine(\
                stem_x, low_y - notehead_offset, \
                stem_x, high_y - notehead_offset)


class staff_item(glyph):
    def __init__(self, midi_codes, dtype, accent):
        # grab config for this class
        self.config = getTheme().staff_item
        super().__init__(self.config.width, self.config.height)

        self.midi_codes = midi_codes
        self.dtype = dtype
        self.accent = accent 

    def canvas_paint_event(self, painter):
        # set font to one that supports unicode for music symbols
        # set the size to match the line spacing on the staff.
        size = self.config.line_spacing
        font = QtGui.QFont("DejaVu Sans", int(size * 1.5))
        painter.setFont(font)

        # draw staff lines using staff_item config
        self.parallel_lines(painter, self.config)

        # draw a chord or a note is len(midi_codes) == 1
        cr = _chord_renderer()
        cr.draw(painter, \
            self.config, self.midi_codes, self.accent, self.dtype) 

