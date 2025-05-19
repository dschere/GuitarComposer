""" 
Creates a dialog that allows a user to describe a series of 
pitch changes used to simulate the bending of a string or a 
whammy bar.

<graph>
    bezier curve describing the string bend

<toggle to activate a slider that adds a control point to the curve>
<set of vertical sliders>




"""
import math
from typing import List, Tuple

from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QHBoxLayout, QGroupBox, QVBoxLayout,
    QSpinBox, QLabel, QListWidget, QButtonGroup, QPushButton, QStyle)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
import view.config as cfg 

from view.events import Signals, StringBendEvent


GRAPH_WIDTH  = 480
GRAPH_HEIGHT = 320 


def data_2_xy(tm, step, ysteps):
    """
    step -> pitch bend steps
    dur  -> tm represents when this bend occurs in time 0-1.0
            this value of time is decimal percentage of the total
            duration of the movement so if its a whole note and tm=0.5
            then the pitch bend occurs at the half note interval.
    """
    r = (GRAPH_HEIGHT / ysteps) 
    y = GRAPH_HEIGHT - (r*step)
    x = int(GRAPH_WIDTH * tm)
    return (x,y) 

def xy_2_data(x, y, ysteps):
    r = (GRAPH_HEIGHT / ysteps)
    step = (GRAPH_HEIGHT-y)/r 
    tm = x / GRAPH_WIDTH 
    return (tm,step) 
 



class GraphPen(QPen):
    def __init__(self, color : Tuple[int,int,int], width: int, ltype):
        super().__init__() 
        self.setColor(QColor(*color))
        print(color)
        self.setWidth(width)
        self.setStyle(ltype)


class BendGraph(QWidget):

    wholeStepPen = GraphPen(cfg.BEND_LINE_COLOR, 3, Qt.PenStyle.SolidLine)
    fractionalStepPen = GraphPen(cfg.BEND_LINE_COLOR, 1, Qt.PenStyle.DashLine)
    pitchChangeTimePen = GraphPen(cfg.BEND_GRID_LINE_COLOR, 3, Qt.PenStyle.SolidLine)
    pitchPointBrush = QBrush(QColor(*cfg.BEND_POINT_COLOR))


    def __init__(self):
        super().__init__()
        self.points = []
        self.ysteps = 2
        self.num_fractional_steps = 4 
        self.moments = 13
        self.margin = 20
        self.point_radius = 17

        self.setFixedWidth(GRAPH_WIDTH)
        self.setFixedHeight(GRAPH_HEIGHT)

    def update_ysteps(self, ysteps): 
        self.ysteps = ysteps
        self.update()

    def update_bend_points(self, points):
        self.points = points 
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.eraseRect(0,0,GRAPH_WIDTH,GRAPH_HEIGHT)

        # draw grid
        n = self.ysteps * self.num_fractional_steps
        for i in range(n+1):
            if i % self.num_fractional_steps == 0:
                painter.setPen(self.wholeStepPen)
            else:
                painter.setPen(self.fractionalStepPen)
            x1 = 0
            y1 = self.margin + int((1 - (i/n)) * GRAPH_HEIGHT)
            x2 = GRAPH_WIDTH
            y2 = y1
            
            painter.drawLine(x1, y1, x2, y2)

        painter.setPen(self.pitchChangeTimePen)
        # connect points 
        if len(self.points) > 0:
            x1 = 0
            y1 = GRAPH_HEIGHT
            for (x2,y2) in self.points:
                painter.drawLine(x1,y1,x2,y2)
                x1 = x2
                y1 = y2

                painter.setBrush(self.pitchPointBrush)
                r = self.point_radius

                painter.drawEllipse(x1-int(r/2),y1-int(r/2),r,r)

            painter.drawLine(x1,y1,GRAPH_WIDTH,y1) 

    def create_string_bend_event(self) -> StringBendEvent:
        """ 
        Map the points to pitch changes
        """
        r = StringBendEvent()
        r.pitch_range = self.ysteps
        for (x,y) in self.points: 
            when_r, semitones = xy_2_data(x,y-self.margin,self.ysteps)
            r.pitch_changes.append((when_r, semitones)) 
        return r

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x1 = event.pos().x()
            y1 = event.pos().y()

            # test to see if this point is within N pixels of any other
            # point if so then this is a delete otherwise its an insert
            N = self.point_radius
            item_index_to_be_deleted = -1 
            for (i,(x2,y2)) in enumerate(self.points):
                d = math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
                if d < N:
                    item_index_to_be_deleted = i 

            if item_index_to_be_deleted != -1:
                # delete operation
                del self.points[item_index_to_be_deleted]
            else:
                # insert and sort by x 
                self.points.append((x1,y1))
                self.points.sort(key=lambda item: item[0])

            # have the window manager trigger the paintEvent()
            self.update()

class BendGraphControlView(QWidget):

    def preset_buttons(self):
        layout = QHBoxLayout()

        # Create a button group
        self.button_group = QButtonGroup(self)

        # Save Button
        save_btn = QPushButton()
        save_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        save_btn.setToolTip("Save")
        self.button_group.addButton(save_btn)
        layout.addWidget(save_btn)

        preview_btn = QPushButton() 
        preview_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)) 
        preview_btn.setToolTip("preview")
        self.button_group.addButton(preview_btn) 
        layout.addWidget(preview_btn)

        # Delete Button
        delete_btn = QPushButton()
        delete_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        delete_btn.setToolTip("Delete")
        self.button_group.addButton(delete_btn)
        layout.addWidget(delete_btn)

        self.preview_btn = preview_btn

        return layout

    def __init__(self, graph: BendGraph):
        super().__init__()
        self.graph = graph 

        group_box = QGroupBox(cfg.BEND_GROUP_TEXT)
        group_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid gray;
                border-radius: 5px; margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; padding: 0 3px;
            }
        """)

        
        group_layout = QVBoxLayout()

        # control the range in steps.
        step_range_label = QLabel() 
        step_range_label.setText(cfg.BEND_RANGE_TEXT)
        group_layout.addWidget(step_range_label)

        self.step_range = QSpinBox()
        self.step_range.setRange(2, 12)  # Set allowed range
        self.step_range.setValue(2)  # Default value
        group_layout.addWidget(self.step_range) 

        # presets 
        presets_label = QLabel() 
        presets_label.setText(cfg.PRESETS_TEXT)
        group_layout.addWidget(presets_label)

        self.preset_list =  QListWidget()
        group_layout.addWidget(self.preset_list) 

        # controls to save/saveas/remove a preset
        group_layout.addLayout(self.preset_buttons())
         
        self.setLayout(group_layout)

    def get_plist(self) -> QListWidget:
        return self.preset_list 

    def on_preview_btn_clicked(self):
        evt = self.graph.create_string_bend_event()
        Signals.preview_pitch_change.emit(evt)


    def setup(self, graph: BendGraph):
        self.preview_btn.clicked.connect(self.on_preview_btn_clicked)
        


class StringBendDialog(QDialog):
    # emitted when a new list of pitch events has been created
    string_bend_selected = pyqtSignal(StringBendEvent) 


    def on_apply(self):
        evt = self.graph.create_string_bend_event() 
        self.string_bend_selected.emit(evt)

    def add_presets(self):
        "Load pre-made bend patterns from a json file" 
        ysteps = self.graph.ysteps

        half_bend = [
            data_2_xy(0.5, 0.5, ysteps)
        ]
        full_bend = [
            data_2_xy(0.5, 1.0, ysteps)
        ]

        self.stock_presets = {
            "half_bend": half_bend,
            "full_bend": full_bend
        } 
        self.custom_presets = {} 

        # self.graph.preset_list
        for n in self.stock_presets:
            self.bctrl_view.get_plist().addItem(n)
            
    def setup(self):
        self.add_presets()
        # assign callbacks to events
        self.bctrl_view.setup(self.graph)

        self.btn_apply.clicked.connect(self.on_apply)

    def clear_clicked(self):
        self.graph.update_bend_points([])

    def cancel_clicked(self):
        self.close()        

    def __init__(self, parent=None):
        super().__init__(parent) 

        layout = QVBoxLayout()

        content_layout = QHBoxLayout() 
        
        self.graph = BendGraph()
        self.bctrl_view = BendGraphControlView(self.graph)
        content_layout.addWidget(self.graph)
        content_layout.addWidget(self.bctrl_view) 

        self.btn_apply = QPushButton("Apply", self)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_clear = QPushButton("Clear", self)

        self.btn_cancel.clicked.connect(self.cancel_clicked)
        self.btn_clear.clicked.connect(self.clear_clicked)

        # Create Button Group
        btn_layout = QHBoxLayout()
        button_group = QButtonGroup(self)
        button_group.addButton(self.btn_apply, 1)
        button_group.addButton(self.btn_clear, 2)
        button_group.addButton(self.btn_cancel, 3)

        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_clear) 
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(content_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # setup controls, load preset data etc.
        self.setup()

def unittest():
    import sys, qdarktheme 

    app = QApplication(sys.argv)

    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    ex = StringBendDialog()
    ex.show() 

    sys.exit(app.exec())


if __name__ == '__main__':
    unittest()        

