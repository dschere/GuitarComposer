""" 
Set up a pattern that changes the variance from fff -> ppp
that changes based on an interval.

Pattern: f, pm, pm, pm
Duration: quarter, eight etc.
Repeat per measure: true|false


^^^
first beat is forte and the rest are pm
"""
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QComboBox, QCheckBox, QPushButton, QLabel
)
from PyQt6.QtCore import pyqtSignal
import sys
from view.events import Signals

from models.measure import DynamicVariance, TabEvent
from music.durationtypes import HALF, QUARTER, EIGHTH, SIXTEENTH
from music.dynamic import *
from view.dialogs.msgboxes import alert

def reverse_dict(d):
    r = {}
    for k, v in d.items():
        r[v] = k
    return r

class DynamicVarianceDialog(QDialog):
    tab_event_updated = pyqtSignal(TabEvent)
    dyn_symbols = {
            "PPP": PPP,
            "PP": PP,
            "P": P,
            "MP": MP,
            "MF": MF,
            "F": F,
            "FF": FF,
            "FFF": FFF
        }
    dyn_symbols_r = reverse_dict(dyn_symbols)
    dur_opts = {
            "half": HALF, 
            "quarter": QUARTER, 
            "eighth": EIGHTH,
            "sixteenth": SIXTEENTH
        }
    dur_opts_r = reverse_dict(dur_opts)
    
    
    def populate(self):
        if self.tab_event.dynamic_variance is not None:
            dv : DynamicVariance = self.tab_event.dynamic_variance
            self.enable_dv.setChecked(dv.isEnabled())

            t = self.dur_opts_r.get(dv.duration)
            if t is not None:
                self.combo.setCurrentText(t)

            dp = list(map(lambda t: self.dyn_symbols_r.get(t,str(t)), dv.dynamic_pattern))
            self.text_edit.setText(" ".join(dp))    
        
            self.checkbox.setChecked(dv.repeat_per_measure)
                

    def __init__(self, tab_event : TabEvent ):
        super().__init__()
        self.setWindowTitle("Dynamic Variance")

        self.tab_event = tab_event 

        # Main layout
        layout = QVBoxLayout(self)

        # Multiline text box
        self.text_edit = QTextEdit(self)
        self.text_edit.setObjectName('pattern')
        layout.addWidget(QLabel("Pattern:"))
        layout.addWidget(self.text_edit)

        # Combo box with selections
        self.combo = QComboBox(self)
        
        self.combo.addItems(["half", "quarter", "eight", "sixteenth"])

        layout.addWidget(QLabel("Select duration:"))
        layout.addWidget(self.combo)

        # Checkbox
        self.checkbox = QCheckBox("Per Measure", self)
        self.checkbox.setObjectName('per_measure')
        layout.addWidget(self.checkbox)

        self.enable_dv = QCheckBox("Enabled", self)
        self.enable_dv.setObjectName('Enabled')
        layout.addWidget(self.enable_dv)

        # populate with 
        self.populate()

        # Ok and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def accept(self) -> None:
        dv = DynamicVariance()

        enabled = self.enable_dv.isChecked()
        if self.tab_event.dynamic_variance is not None:
            self.tab_event.dynamic_variance.enabled = enabled
        if enabled is False:
            # In the case where there was no existed dynamic_variance this
            # is like a cancel, otherwise we alreay set the enabled to false
            # so there nothing to do
            return 

        dv.enabled = enabled           

        pattern = self.text_edit.toPlainText()
        for token in pattern.upper().split():
            v = self.dyn_symbols.get(token)
            if v is None:
                if token.isdigit() and int(token) < 128:
                    v = int(token)
                else:
                    choices = list(self.dyn_symbols.keys())
                    choices.sort()
                    c = ",".join(choices)
                    alert(f"{token} must be one of {c} or a number 1-127!")
                    return
            dv.dynamic_pattern.append(v)

        duration = self.combo.currentText()
        per_measure = self.checkbox.isChecked()

        dv.duration = self.dur_opts[duration]
        dv.repeat_per_measure = per_measure
        
        self.tab_event.dynamic_variance = dv 
        
        self.tab_event_updated.emit(self.tab_event)

        return super().accept()
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    te = TabEvent(6)
    dialog = DynamicVarianceDialog(te)
    if dialog.exec():
        pattern = dialog.text_edit.toPlainText()
        duration = dialog.combo.currentText()
        per_measure = dialog.checkbox.isChecked()
        print("Pattern:", pattern)
        print("Duration:", duration)
        print("Per Measure:", per_measure)
        if te.dynamic_variance:
            print(vars(te.dynamic_variance))
        else:
            print("dynamic varince not set")    
    sys.exit(app.exec())

