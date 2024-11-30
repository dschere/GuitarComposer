""" 
draws the squiggly lines for vibrato, the updown arrows for chords strokes
along with other musical graphic oddities ...
"""
from view.editor.glyphs.canvas import Canvas
from view.editor.glyphs.common import STAFF_SYM_WIDTH, ORNAMENT_MARKING_HEIGHT
from models.track import TabCursor
from PyQt6.QtGui import QPainter

class oramental_markings(Canvas):
    """ 
    This widget is used to paint markings between the tab and the staff.
    These would be slide, bend, stroke and other visual performance 
    queues.     
    """
    def __init__(self, tab_cursor: TabCursor):
        super().__init__(STAFF_SYM_WIDTH,ORNAMENT_MARKING_HEIGHT)
        self.tab_cursor = tab_cursor

    def _draw_downstroke(self, painter: QPainter):
        """ 
        Draw a down arrow on the right side of the tab 
        """
        x = int(STAFF_SYM_WIDTH/2)
        start_y = 0
        end_y = ORNAMENT_MARKING_HEIGHT-1
        painter.drawLine(x, start_y, x, end_y)
        painter.drawLine(x, end_y, 8, end_y-3)
        painter.drawLine(x, end_y, 2, end_y-3)

    def _draw_upstroke(self, painter: QPainter):
        x = int(STAFF_SYM_WIDTH/2)
        start_y = 0
        end_y = ORNAMENT_MARKING_HEIGHT-1
        painter.drawLine(x, end_y, x, start_y)
        painter.drawLine(x, start_y, 8, start_y+3)
        painter.drawLine(x, start_y, 2, start_y+3)

    def draw_vibrato(self):
        pass

    def draw_bend(self):
        pass

    def draw_prebend_release(self):
        pass

    def draw_legato(self):
        pass

    def draw_staccato(self):
        pass

    # override to capture paint event
    def canvas_paint_event(self, painter):
        pass