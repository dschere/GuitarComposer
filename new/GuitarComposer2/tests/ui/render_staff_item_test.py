"""
Exercise rendering of staff items such as notes and chords. 
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QLabel

from guitarcomposer.ui.widgets.glyphs.staff_item import staff_item
from guitarcomposer.ui.widgets.glyphs.staff_header import staff_header
from guitarcomposer.ui.widgets.glyphs.staff_measure_divider import staff_measure_divider
from guitarcomposer.ui.widgets.glyphs.constants import *

from guitarcomposer.common.durationtypes import *

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Layout Example")
        self.setGeometry(100, 100, 600, 200)

        central_widget = QWidget()  # Central widget to hold the layout
        self.setCentralWidget(central_widget)

        # Create a grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        grid_layout.setVerticalSpacing(0) 
        central_widget.setLayout(grid_layout)


        grid_layout.addWidget(\
            staff_header(TREBLE_CLEFF, 120, (4,4), \
               [(SHARP_SIGN,90),(SHARP_SIGN,85)] ), 0, 0) 

        grid_layout.addWidget(staff_measure_divider(BARLINE2), 0, 1)


        dtype = QUARTER
        accent = SHARP_SIGN
        midi_codes = [101]
        grid_layout.addWidget(\
            staff_item(midi_codes, dtype, accent, TREBLE_CLEFF), 0, 2)

        dtype = HALF
        accent = SHARP_SIGN
        midi_codes = [78, 71, 55]
        grid_layout.addWidget(\
            staff_item(midi_codes, dtype, accent, TREBLE_CLEFF), 0, 3)

        dtype = SIXTEENTH
        accent = FLAT_SIGN
        midi_codes = [78, 71, 63]
        grid_layout.addWidget(\
            staff_item(midi_codes, dtype, accent, TREBLE_CLEFF), 0, 4)


        # adding a widget at end suddenly makes the setHorizontalSpacing
        # work ;(
        grid_layout.addWidget(QLabel(""), 0, 5)         


def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
