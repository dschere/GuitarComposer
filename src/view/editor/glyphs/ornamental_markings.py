""" 
draws the squiggly lines for vibrato, the updown arrows for chords strokes
along with other musical graphic oddities ...


dynamic change
hand effect / stroke

"""
from view.editor.glyphs.canvas import Canvas
from view.editor.glyphs.common import (ORNAMENT_Y, 
                                       STAFF_SYM_WIDTH, 
                                       ORNAMENT_MARKING_HEIGHT, 
                                       LEGATO, 
                                       STACCATO, DOWNSTROKE, UPSTROKE)
from models.track import TabCursor
from PyQt6.QtGui import QPainter
import math

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
    def __init__(self, tab_cursor: TabCursor):
        super().__init__(STAFF_SYM_WIDTH,ORNAMENT_MARKING_HEIGHT)
        self.tab_cursor = tab_cursor

    
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

    def _draw_bend(self, painter: QPainter):
        """
        Draw a curve based on the pitch bend histogram.

        Use the high/low to scale the curve. 
        """
        high = self.tab_cursor.pitch_bend_histogram[0]
        low = high
        points = []

        for b in self.tab_cursor.pitch_bend_histogram[1:]:
            if b > high:
                high = b
            if b < low:
                low = b

        span = (high - low)
        n = STAFF_SYM_WIDTH / len(self.tab_cursor.pitch_bend_histogram) 
        for (i,b) in enumerate(self.tab_cursor.pitch_bend_histogram):
            x = int(i * n)
            y = ((high - b) / span) * ORNAMENT_MARKING_HEIGHT
            points.append((x,y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

    def _draw_marker(self, painter: QPainter, text):
        self.draw_symbol(painter, text, x=10, y=ORNAMENT_Y, draw_lines=False) 
        

    # override to capture paint event
    def canvas_paint_event(self, painter):
        if self.tab_cursor.legato == True: 
            self._draw_marker(painter, LEGATO)
        elif self.tab_cursor.staccato:
            self._draw_marker(painter, STACCATO)

        if self.tab_cursor.pitch_bend_active:
            self._draw_bend(painter)
        elif self.tab_cursor.downstroke:
            self._draw_marker(painter, DOWNSTROKE) 
        elif self.tab_cursor.upstroke:
            self._draw_marker(painter, UPSTROKE)
        