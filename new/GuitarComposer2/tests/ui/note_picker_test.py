import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QLabel

from guitarcomposer.ui.widgets.note_picker import note_picker
from guitarcomposer.ui.widgets.dynamic_control import dynamic_control
from guitarcomposer.ui.widgets.duration_control import duration_control

from guitarcomposer.ui.widgets.glyphs.constants import *


def selected_cb(selected):
    print("Note selected: " + selected)

class MyWindow(QMainWindow):

     
    def __init__(self):
        super().__init__()
        self.setWindowTitle("note picker mockup")
        #self.setGeometry(100, 100, 600, 200)

        central_widget = QWidget()  # Central widget to hold the layout
        self.setCentralWidget(central_widget)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        grid_layout.setVerticalSpacing(0) 
        central_widget.setLayout(grid_layout)

        def on_selected(dyn_text, dyn_value):
            print("%s %d" % (dyn_text, dyn_value))

        dc = dynamic_control(on_selected)
        grid_layout.addWidget(dc, 0, 0)
        dc.select("MF")

       
        dur_ctl = duration_control(selected_cb)
        grid_layout.addWidget(dur_ctl, 0, 1)  
        dur_ctl.select(QUATER_REST)


def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

