"""
Simple array of mutually exclusive buttons that allows for navigation when the score
spans a large number of measures. 

This is a good widget to assign colors and tool tip text in the future which could mark
events in the peice such as the start of a chorus or a transition.

"""
from PyQt6.QtWidgets import (
    QWidget, QPushButton,
    QGridLayout, QButtonGroup, QAbstractButton
)
from PyQt6.QtCore import QSize
from view.events import Signals, EditorEvent, Track
from util.layoutRemoveAllItems import layoutRemoveAllItems
from PyQt6.QtCore import pyqtSignal

class MeasureNavigation(QWidget):
    measure_change = pyqtSignal(int)

    def editor_event(self, evt):
        if self.prev_num_measures != len(self.track_model.measures):
            self.setup()
            self.prev_num_measures = self.track_model.measures

    # setup handler for when measure is selected.
    def click_handler(self, b: QAbstractButton):
        midx = self.button_group.id(b)
        self.measure_change.emit(midx)

    def set_measure(self, midx):
        try: 
            self.button_group.buttonClicked.disconnect(self.click_handler)        
        except TypeError:
            pass

        b : QAbstractButton | None = self.button_group.button(midx)
        if b is not None:
            b.click()

        self.button_group.buttonClicked.connect(self.click_handler)

    def setup(self):
        track = self.track_model
        try: 
            self.button_group.buttonClicked.disconnect(self.click_handler)        
        except TypeError:
            pass

        # remove all buttons

        # rebuilt array
        w = 30
        max_cols = int(self.width() / w)
        row = 0
        col = 0
        for (i,m) in enumerate(track.measures):
            btn = self.button_group.button(i)
            if btn is None:
                btn = QPushButton(self)
                btn.setText(f"{(i+1) % 100}")
                if i >= 99:
                    btn.setToolTip(f"{i+1}")
                btn.setCheckable(True)  # makes it toggleable
                btn.setFixedSize(QSize(w, w))  # small square buttons
                btn.move(col * w, row * w) 
                #layout.addWidget(btn, row, col)
                self.button_group.addButton(btn, id=i)
                btn.show()

            if track.current_measure == i:
                btn.setChecked(True)

            
            if col+1 < max_cols:
                col += 1
            else:
                col = 0
                row += 1

        # In the case that measure where removed.
        i = len(track.measures)
        while True:
            button = self.button_group.button(i)
            if button is not None:
                self.button_group.removeButton(button)
                button.deleteLater() # Delete the button object
                i += 1
            else:
                break


        self.button_group.buttonClicked.connect(self.click_handler)        
        self.setFixedHeight((row + 1)* w)


    def __init__(self, parent, track_model: Track):
        super().__init__(parent)
        self.setMinimumWidth(400)

        self.track_model = track_model
        self.prev_num_measures = len(self.track_model.measures)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        Signals.editor_event.connect(self.editor_event)

        self.setup()
        