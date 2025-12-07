""" 
Helper dialog that allows the user to select midi drum 
codes. 

cursor move -> sets current tab event 
user selects -> update tab event then update the tab presenter.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMenuBar, QMenu
from PyQt6.QtGui import QAction
from models.measure import TabEvent

from util.drums import DrumDatabase

from view.events import Signals, EditorEvent


class DrumCodeDialog(QDialog):
    db = DrumDatabase()

    def selected(self, key_code):
        evt = EditorEvent(EditorEvent.DRUM_DIALOG_SELECT)
        evt.midi_drum_code = key_code
        Signals.editor_event.emit(evt)

    def create_action(self, drum_class, key_code, desc):
        action = QAction(desc + f" ({key_code})", drum_class)
        action.triggered.connect(lambda : self.selected(key_code))
        return action 
    
    def createUi(self):
        """
        Create a grid of comboxes for each type of percussion, mu
        """
        top_layout = QVBoxLayout()
        mbar = QMenuBar()
        drum_tree = QMenu("Midi Codes",mbar)
        mbar.addMenu(drum_tree)

        for group_name in self.db.groups():
            drum_class = QMenu(group_name, self)
            for (key_code, desc) in self.db.drumData(group_name):
                drum_class.addAction(self.create_action(drum_class, key_code, desc))
            drum_tree.addMenu(drum_class)
        top_layout.addWidget(mbar)
        self.setLayout(top_layout)


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Midi Drim Codes Helper")
        self.setToolTip("Select from this meno to insert midi codes to the current tab selection.")
        self.createUi()

def main():
    import sys, logging, qdarktheme
    from PyQt6.QtWidgets import QApplication
    logging.debug("Running with debug log level")

    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)


    dialog = DrumCodeDialog()
    dialog.show()

    sys.exit(app.exec())  # <- main event loop
    

if __name__ == '__main__':
    main()
