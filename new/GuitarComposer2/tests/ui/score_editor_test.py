import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QLabel


from guitarcomposer.ui.widgets.score_editor import score_editor_view
from guitarcomposer.ui.editor.controller import editor_controller

from guitarcomposer.ui.widgets.glyphs.constants import *


def selected_cb(selected):
    print("Note selected: " + selected)

class MyWindow(QMainWindow):

     
    def __init__(self):
        super().__init__()
        self.setWindowTitle("score editor")
        #self.setGeometry(100, 100, 600, 400)

        ec = editor_controller()
        sev = score_editor_view(ec)


        self.setCentralWidget(sev)



def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()


