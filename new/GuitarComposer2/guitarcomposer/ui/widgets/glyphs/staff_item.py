from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *
from .note_renderer import note_renderer

from guitarcomposer.common import durationtypes as DT
from guitarcomposer.ui.config import config


class chord_renderer:
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

    def __init__(self, cleff):
        self.cleff = cleff

    def draw_floating_lines(self, painter, conf, note_y):
        line_spacing = conf.line_spacing
        num_lines = conf.num_lines
        y_start = conf.y_start
        accent_spacing = conf.accent_spacing
        width = conf.width
        y_end = y_start + ((num_lines-1) * line_spacing)

        painter.setPen(QtGui.QPen(Qt.GlobalColor.black, 1))

        y = y_start
        # if the highest note is above the highest line on the
        # staff draw flowing lines
        while note_y < (y - (line_spacing/2)):
            y -= line_spacing
            x1 = accent_spacing
            x2 = width - accent_spacing
            painter.drawLine(x1, y, x2, y)

        y = y_end
        while note_y > (y + (line_spacing/2)):
            y += line_spacing
            x1 = accent_spacing
            x2 = width - accent_spacing
            painter.drawLine(x1, y, x2, y)

    def draw_rest(self, dtype):
        nr = note_renderer(self.cleff)
        nr.draw_rest(dtype)
        
        
    def draw(self, painter, conf, midi_codes, accent, dtype):
        if len(midi_codes) == 0:
            self.draw_rest(dtype)
            return

        # arrange midi codes highest to lowest
        if len(midi_codes) > 1:
            midi_codes.sort()
            midi_codes.reverse()

        nr = note_renderer(self.cleff)
        midi_code = midi_codes[0]
        nr.draw_note(
            painter, conf, midi_code, accent, dtype)

        for midi_code in midi_codes[1:]:
            nr.draw_notehead(
                painter, conf, midi_code, accent, dtype)

        # draw lines above/below staff if the note falls outside.
        high_y = nr.get_y_coord(
            midi_codes[0], conf, accent)
        self.draw_floating_lines(painter, conf, high_y)
        if len(midi_codes) > 1:
            low_y = nr.get_y_coord(
                midi_codes[-1], conf, accent)
            # draw lines above/below staff if the note falls outside.
            self.draw_floating_lines(painter, conf, low_y)

        # draw the verticle stem line connecting the notes
        if len(midi_codes) > 1 and dtype not in (DT.WHOLE, DT.HALF):
            # configure a 2 pixel wide verticle line
            painter.setPen(QtGui.QPen(Qt.GlobalColor.black, 1))

            # draw a line connecting the notes is dtype is not
            # a whole or half note.
            line_spacing = conf.line_spacing
            accent_spacing = conf.accent_spacing
            text_font_size = conf.text_font_size
            stem_x = conf.chord_stem_x

            notehead_offset = int(text_font_size/7)
            painter.drawLine(
                stem_x, low_y - notehead_offset,
                stem_x, high_y - notehead_offset)


class staff_item(glyph):
    def __init__(self, midi_codes, dtype, accent, staff):
        # grab config for this class
        self.config = config().staff_item
        super().__init__(self.config.width, self.config.height)

        self.midi_codes = midi_codes
        self.dtype = dtype
        self.accent = accent
        self.staff = staff

    def canvas_paint_event(self, painter):
        # set font to one that supports unicode for music symbols
        # set the size to match the line spacing on the staff.
        size = self.config.line_spacing
        text_font_size = self.config.text_font_size
        text_font = self.config.text_font
        font = QtGui.QFont(text_font, text_font_size)
        painter.setFont(font)

        # draw staff lines using staff_item config
        self.parallel_lines(painter, self.config)

        # draw a chord or a note is len(midi_codes) == 1
        cr = chord_renderer(self.staff)
        cr.draw(painter,
                self.config, self.midi_codes, self.accent, self.dtype)
