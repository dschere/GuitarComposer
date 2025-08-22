""" 
draws the squiggly lines for vibrato, the updown arrows for chords strokes
along with other musical graphic indicators


dynamic change
hand effect / stroke
vibrato
lagato/staccato

"""
from music.constants import Dynamic
from view.dialogs.stringBendDialog import StringBendDialog
from view.editor.glyphs.canvas import Canvas
from view.editor.glyphs.common import (BEND_SYMBOL, NO_ARTICULATION, ORNAMENT_ARTICULATION_Y, ORNAMENT_BEND_Y, ORNAMENT_DYNAMIC_Y, ORNAMENT_FONT_SIZE, ORNAMENT_STROKE_Y, ORNAMENT_Y, 
                                       STAFF_SYM_WIDTH, 
                                       ORNAMENT_MARKING_HEIGHT, 
                                       LEGATO, 
                                       STACCATO, DOWNSTROKE, UPSTROKE)
from models.track import TabEvent
from PyQt6.QtGui import QPainter, QFont
import math
from view.config import GuitarFretboardStyle

from view.events import StringBendEvent

def draw_sine_wave(painter : QPainter, **conf):
    # Dimensions and scaling
    amplitude = conf.get('amplitude',5)   # Amplitude of the sine wave (horizontal span)
    wavelength = conf.get('wavelength',20)  # Wavelength of the sine wave (vertical span)
    center_x = conf['width'] // 2  # Center X for the wave
    center_y = conf['height'] // 2 

    # Draw the sine wave
    points = []
    if conf.get('orientation','verticle') == 'verticle':
        for y in range(0, conf['height']):  # Iterate over the height
            x = center_x + amplitude * math.sin(2 * math.pi * y / wavelength)
            x = int(x)
            points.append((x, y))
    else:
        # horizontal
        for x in range(0, conf['width']):  # Iterate over the height
            y = center_y + amplitude * math.sin(2 * math.pi * x / wavelength)
            y = int(y)
            points.append((x, y))

    # Draw the wave using the points
    for i in range(len(points) - 1):
        painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])


class oramental_markings(Canvas):
    """ 
    This widget is used to paint markings between the tab and the staff.
    These would be slide, bend, stroke and other visual performance 
    queues.     
    """
    def __init__(self, tab_event: TabEvent):
        super().__init__(STAFF_SYM_WIDTH,ORNAMENT_MARKING_HEIGHT)
        self.tab_event = tab_event
        self.stroke_color = GuitarFretboardStyle.string_color_rgb

    def on_stringBendDialog_apply(self, evt : StringBendEvent):
        self.tab_event.pitch_changes = evt.pitch_changes 
        self.tab_event.pitch_range = evt.pitch_range
        self.tab_event.points = evt.points # type: ignore
        self.tab_event.pitch_bend_active = len(evt.pitch_changes) > 0

    def mousePressEvent(self, event):
        # Get the x, y coordinates of the mouse click
        x = event.position().x()
        y = event.position().y()

        if y <= ORNAMENT_BEND_Y and self.tab_event.pitch_bend_active:
            # mouse click over the bend sign.        
            # create dialog allow it to manipulate 'te'
            dialog = StringBendDialog(self, self.tab_event)
            dialog.string_bend_selected.connect(self.on_stringBendDialog_apply)
            dialog.show()

    
    # def _draw_downstroke(self, painter: QPainter):
    #     """ 
    #     Draw a down arrow on the right side of the tab 
    #     """
    #     x = int(STAFF_SYM_WIDTH/2)
    #     start_y = ORNAMENT_Y
    #     end_y = ORNAMENT_MARKING_HEIGHT-1
    #     painter.drawLine(x, start_y, x, end_y)
    #     painter.drawLine(x, end_y, 8, end_y-3)
    #     painter.drawLine(x, end_y, 2, end_y-3)

    # def _draw_upstroke(self, painter: QPainter):
    #     x = int(STAFF_SYM_WIDTH/2)
    #     start_y = ORNAMENT_Y
    #     end_y = ORNAMENT_MARKING_HEIGHT-1
    #     painter.drawLine(x, end_y, x, start_y)
    #     painter.drawLine(x, start_y, 8, start_y+3)
    #     painter.drawLine(x, start_y, 2, start_y+3)

    def _draw_vibrato(self, painter: QPainter):
        draw_sine_wave(painter, 
            width=self.width(),
            height=self.height(),
            orientation='horizontal',
            wavelength=13
        )

    def _draw_gliss(self, painter: QPainter):
        draw_sine_wave(painter, 
            width=self.width()/4,
            height=self.height(),
            orientation='veritical',
            wavelength=13
        )

    # def _draw_bend(self, painter: QPainter):
    #     """
    #     Draw a curve based on the pitch bend histogram.

    #     Use the high/low to scale the curve. 


    #     tab_event.pitch_changes = [(0-1.0,0-<pitch_range>),...]
    #     """
    #     high = None
    #     low = None
    #     points = []

    #     for (when_r, semitones) in self.tab_event.pitch_changes:
    #         if high is None:
    #             high = semitones
    #             low = semitones
    #         else:
    #             if semitones > high:
    #                 high = semitones
    #             if semitones < low:
    #                 low = semitones

    #     assert(high)
    #     assert(low)
    #     span = (high - low)
    #     n = STAFF_SYM_WIDTH / len(self.tab_event.pitch_changes) 
    #     for (when_r,semitones) in enumerate(self.tab_event.pitch_changes):
    #         x = when_r * STAFF_SYM_WIDTH
    #         y = ((high - semitones) / span) * ORNAMENT_MARKING_HEIGHT
    #         points.append((x,y))

    #     for i in range(len(points) - 1):
    #         painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

    def _draw_marker(self, painter: QPainter, text, y):
        self.draw_symbol(painter, text, x=10, y=y, draw_lines=False) 
        

    # override to capture paint event
    def canvas_paint_event(self, painter : QPainter):        
        if self.tab_event.legato: 
            self._draw_marker(painter, LEGATO, ORNAMENT_ARTICULATION_Y)
        elif self.tab_event.staccato:
            self._draw_marker(painter, STACCATO, ORNAMENT_ARTICULATION_Y)
        elif self.tab_event.render_clear_articulation:
            self.draw_symbol(painter, NO_ARTICULATION, x=20, draw_lines=False, 
                    y=ORNAMENT_ARTICULATION_Y, size=16)

        if self.tab_event.pitch_bend_active:
            self._draw_marker(painter, BEND_SYMBOL, ORNAMENT_BEND_Y)

        if self.tab_event.downstroke:
            self.draw_symbol(painter, DOWNSTROKE,x=10, 
                    y=ORNAMENT_STROKE_Y, draw_lines=False, color=self.stroke_color) 
        elif self.tab_event.upstroke:
            self.draw_symbol(painter, UPSTROKE,x=10, 
                    y=ORNAMENT_STROKE_Y, draw_lines=False, color=self.stroke_color) 
        
        if self.tab_event.render_dynamic:
            t = Dynamic.short_text(self.tab_event.dynamic)
            self.draw_symbol(painter, t, x=20, y=ORNAMENT_DYNAMIC_Y, 
                draw_lines=False, size=10, italic=True, color=(255, 215, 0)) 
            
            