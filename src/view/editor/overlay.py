"""
This is an overlay widget on top of the trackPresenter. It is meant as 
a canvas for drawing on top of the staff glyphs that span moments in
a score such as tied notes, legato etc. 

"""
import logging
from typing import List, Tuple
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF 
from PyQt6.QtGui import QPainter, QPen, QPalette, QPainterPath

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QScrollArea)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor

from view.editor.measurePresenter import MeasurePresenter
from view.editor.tabEventPresenter import TabEventPresenter


from models.measure import Measure, TabEvent, TUPLET_DISABLED
from models.track import Track
from view.config import GuitarFretboardStyle

from view.editor.glyphs.common import STAFF_SYM_WIDTH


class TiedNoteRederer:
    def __init__(self, overlay: 'OverlayWidget'): 
        self.overlay = overlay 
        self.prev_te : TabEvent | None = None
        self.prev_mp : MeasurePresenter | None = None 

    def draw_tied_note(self, y, tp_start: TabEventPresenter, tp_end: TabEventPresenter):
        w : QWidget = self.overlay.parent   # type: ignore

        start = tp_start.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y-10))
        ctrl1 = tp_start.mapTo(w, QPointF(STAFF_SYM_WIDTH/2+15,y-25))
        end   = tp_end.mapTo(w, QPointF(STAFF_SYM_WIDTH/2, y-10))
        ctrl2 = tp_end.mapTo(w, QPointF(STAFF_SYM_WIDTH/2-15, y-25))

        self.overlay.add_beizer_line2(start, end, ctrl1, ctrl2)    

    def on_tab_event(self, tab_event: TabEvent, mp: MeasurePresenter):
        if self.prev_te is not None and \
           self.prev_mp is not None and \
           sum(tab_event.tied_notes) != 0:
            tp_start = self.prev_mp.tab_map[self.prev_te]
            tp_end = mp.tab_map[tab_event] 
            for (gstr, tied) in enumerate(tab_event.tied_notes):
                if tied:
                    y = tab_event.note_ypos[gstr]
                    # add beizer line that ties two notes.
                    self.draw_tied_note(y, tp_start, tp_end)
        
        self.prev_te = tab_event
        self.prev_mp = mp 

""" 
Todo create a renderer for tuplet groups.

above the highest note in the set.
 _________ <number> _______
|                          |    

"""

class TupletGroup:
    def __init__(self):
        self.tuplet_code = -1
        self.tab_events : List[Tuple[TabEvent, TabEventPresenter]] = []
        

    def add(self, te: TabEvent, mp: MeasurePresenter):
        self.tab_events.append( (te, mp.tab_map[te]) )

    def compute_line_y(self):
        s = set()
        for (te, _) in self.tab_events:
            s.add(te.minimum_y_pos_for_tuplet_line())
        r = min(s)
        if r < 100:
            return r
        return 100
    
    def render_line(self, painter: QPainter, overlay: 'OverlayWidget'):
        w : QWidget = overlay.parent   # type: ignore
        y = self.compute_line_y()
        start_te, start_tp = self.tab_events[0]
        end_te, end_tp = self.tab_events[-1]

        line_points = []
        #start = tp_start.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y-10))
        #start = tp_start.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y-10))
        pt1 = start_tp.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y+5))
        pt2 = start_tp.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y))


        pt3 = end_tp.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y))
        pt4 = end_tp.mapTo(w, QPointF(STAFF_SYM_WIDTH/2,y+5))
        
        text_x_pos = (pt3.x() - pt2.x())/2 + pt2.x() - 4
        text_y_pos = pt3.y() - 3

        painter.drawLine(pt1, pt2)
        painter.drawLine(pt2, pt3)
        painter.drawLine(pt3, pt4)
        painter.drawText(int(text_x_pos), int(text_y_pos), str(self.tuplet_code))
        


class TupletGroupRederer:
    def __init__(self, overlay: 'OverlayWidget'): 
        self.overlay = overlay 
        self.tuplet_group = []
        self.current_tuple_group = None 

    def reset(self):
        self.tuplet_group = []
        self.current_tuple_group = None 

    def on_paint(self, painter: QPainter):
        for tg in self.tuplet_group:
            tg.render_line(painter, self.overlay)
            

    def on_tab_event(self, tab_event: TabEvent, mp: MeasurePresenter):

        # New tuplet encountered
        if self.current_tuple_group is None and tab_event.tuplet_code != TUPLET_DISABLED:
            # new tuplet group
            tg = TupletGroup()
            tg.tuplet_code = tab_event.tuplet_code
            tg.add(tab_event, mp)
            self.current_tuple_group = tg 
            
        elif isinstance(self.current_tuple_group, TupletGroup):
            if tab_event.tuplet_code == self.current_tuple_group.tuplet_code:
                self.current_tuple_group.add(tab_event, mp)
            else:
                self.tuplet_group.append(self.current_tuple_group)
                if self.current_tuple_group.tuplet_code == TUPLET_DISABLED:
                    self.current_tuple_group = None
                else:
                    tg = TupletGroup()
                    tg.tuplet_code = tab_event.tuplet_code
                    tg.add(tab_event, mp)
                    self.current_tuple_group = tg 

    


class OverlayWidget(QWidget):
    """ 
    Draws images on top of the track staff such as tied notes (and one day lagato)
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.resize(parent.size())
        self.parent = parent

        # todo make this configurable.
        self.pen_color = QColor(*GuitarFretboardStyle.string_color_rgb)

        # list of beizer lines to be drawn to represent tied 
        # notes or legato 
        self.beizer_lines : List[List[QPointF]] = []    

        self.tgr = TupletGroupRederer(self)

    def clear_beizer_lines(self):
        self.beizer_lines : List[List[QPointF]] = []

    def add_beizer_line(self, start: QPointF, end: QPointF, ctrl1: QPointF):
        self.beizer_lines.append([start,end,ctrl1])

    def add_beizer_line2(self, start: QPointF, end: QPointF, ctrl1: QPointF, ctrl2: QPointF):
        self.beizer_lines.append([start,end,ctrl1,ctrl2])

    def setup(self, track_model: Track, mp_map):
        self.clear_beizer_lines()
        tnr = TiedNoteRederer(self)
        self.tgr.reset()

        for measure in track_model.measures:
            mp : MeasurePresenter = mp_map[measure]
            for te in measure.tab_events:
                tab_event : TabEvent = te

                # populate beizer line array for tied notes. 
                tnr.on_tab_event(tab_event, mp)
                self.tgr.on_tab_event(tab_event, mp)

        # schedule a paintEvent to render beizer curves.
        self.update()          

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen()
        pen.setColor(self.pen_color)
        painter.setPen(pen)

        # paint tuplet markings 
        self.tgr.on_paint(painter)
        for b_pts in self.beizer_lines:
            path = QPainterPath()
            start = b_pts[0]
            end = b_pts[1]

            path.moveTo(start)

            if len(b_pts) == 4:
                ctrl1 = b_pts[2]
                ctrl2 = b_pts[3]
                path.cubicTo(ctrl1, ctrl2, end)
            else:
                ctrl1 = b_pts[2]
                path.quadTo(ctrl1, end)

            painter.drawPath(path)
        

        painter.end()
