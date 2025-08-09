"""
This is an overlay widget on top of the trackPresenter. It is meant as 
a canvas for drawing on top of the staff glyphs that span moments in
a score such as tied notes, legato etc. 

"""
from typing import List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF 
from PyQt6.QtGui import QPainter, QPen, QPalette, QPainterPath

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QScrollArea)
from PyQt6.QtCore import Qt, QPointF

from view.editor.measurePresenter import MeasurePresenter
from view.editor.tabEventPresenter import TabEventPresenter


from models.measure import Measure, TabEvent
from models.track import Track


class TiedNoteRederer:
    def __init__(self, overlay: 'OverlayWidget'):
        self.start_tied : TabEvent | None = None
        self.overlay = overlay 

    def draw_tied_note(self, y, tp_start: TabEventPresenter, tp_end: TabEventPresenter):
        w : QWidget = self.overlay.parent   # type: ignore

        start = tp_start.mapTo(w, QPointF(0,y))
        ctrl1 = tp_start.mapTo(w, QPointF(15,y-15))
        end   = tp_end.mapTo(w, QPointF(0, y))
        ctrl2 = tp_end.mapTo(w, QPointF(-15, y-15))

        self.overlay.add_beizer_line2(start, end, ctrl1, ctrl2)    

    def on_tab_event(self, tab_event: TabEvent, mp: MeasurePresenter):
        if self.start_tied is None:
            if sum(tab_event.tied_notes) != 0:
                self.start_tied = tab_event
        else:
            tp_start = mp.tab_map[self.start_tied] 
            tp_end = mp.tab_map[tab_event]
            for (gstr, tied) in enumerate(self.start_tied.tied_notes):
                if tied:
                    y = self.start_tied.note_ypos[gstr]
                    # add beizer line that ties two notes.
                    self.draw_tied_note(y, tp_start, tp_end)
            
            if sum(tab_event.tied_notes) != 0:
                start_tied = tab_event
            else:
                start_tied = None
            
            


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
        palette = self.palette()
        self.pen_color = palette.color(QPalette.ColorRole.WindowText)

        # list of beizer lines to be drawn to represent tied 
        # notes or legato 
        self.beizer_lines : List[List[QPointF]] = []    

    def clear_beizer_lines(self):
        self.beizer_lines : List[List[QPointF]] = []

    def add_beizer_line(self, start: QPointF, end: QPointF, ctrl1: QPointF):
        self.beizer_lines.append([start,end,ctrl1])

    def add_beizer_line2(self, start: QPointF, end: QPointF, ctrl1: QPointF, ctrl2: QPointF):
        self.beizer_lines.append([start,end,ctrl1,ctrl2])

    def setup(self, track_model: Track, mp_map):
        self.clear_beizer_lines()
        tnr = TiedNoteRederer(self)

        for measure in track_model.measures:
            mp : MeasurePresenter = mp_map[measure]
            for te in measure.tab_events:
                tab_event : TabEvent = te

                # populate beizer line array for tied notes. 
                tnr.on_tab_event(tab_event, mp)

        # schedule a paintEvent to render beizer curves.
        self.update()          

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen()
        pen.setColor(self.pen_color)
        painter.setPen(pen)
        
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
