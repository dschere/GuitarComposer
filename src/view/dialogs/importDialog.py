"""
Import midi files 
"""
import os
import pathlib
import tempfile
import requests

from models.song import Song
from util.iotools.load_midi import load_midi
from view.events import Signals, ProgressEvent



import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDialog, 
                             QVBoxLayout, QLabel, QLineEdit,QProgressBar,
                             QPushButton, QDialogButtonBox, QGridLayout, 
                             QPushButton, QFileDialog)
from PyQt6.QtGui import QIcon


class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Data")
        
        layout = QVBoxLayout(self)

        fields_layout = QGridLayout(self)
        
        self.label = QLabel("URL:")
        self.input_url = QLineEdit()

        open_file_button = QPushButton()
        open_file_button.setText("Open File")
        open_file_button.setIcon(QIcon.fromTheme("document-open")) 
        open_file_button.clicked.connect(self.open_file_dialog)

        fields_layout.addWidget(self.label, 0,0)
        fields_layout.addWidget(self.input_url, 0,1)
        fields_layout.addWidget(open_file_button,0,2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.message_text = QLabel(self)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        fields_layout.addWidget(self.message_text,1,0,1,3)
        fields_layout.addWidget(self.progress,2,0,2,3)
                

        
        buttons.accepted.connect(self.run)  # Closes and returns QDialog.DialogCode.Accepted
        buttons.rejected.connect(self.reject)  # Closes and returns QDialog.DialogCode.Rejected
        
        
        layout.addLayout(fields_layout)
        layout.addWidget(buttons)

        Signals.progress_event.connect(self.parser_feedback)

    def __del__(self):
        Signals.progress_event.disconnect(self.parser_feedback)

    def open_file_dialog(self):
        # Get the file name using the static method
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Midi Files (*.mid)"
        )

        if file_name:
            self.input_url.setText(file_name)
            
    def parser_feedback(self, evt: ProgressEvent):
        if evt.sender_id == "load_midi":
            self.message_text.setStyleSheet(
                {
                    logging.ERROR: "color: red;",
                    logging.WARNING: "color: yellow;"
                }.get(evt.severity,"")
            )
            self.message_text.setText(evt.msg)
            if evt.value != -1.0:
                self.progress.setValue(int(evt.value))
            self.update()

    def run_download(self, url) -> Song | None:
        s = None 
        try:
            evt = ProgressEvent("load_midi", logging.INFO, f"loading {url}")
            self.parser_feedback(evt)
            r = requests.get(url)
            (fd, filename) = tempfile.mkstemp()
            os.close(fd)

            n = open(filename,"wb").write(r.content)
            assert(n == len(r.content))
            
            s = load_midi(filename)
            os.remove(filename)
        except Exception as e:
            evt = ProgressEvent("load_midi", logging.ERROR, str(e))
            self.parser_feedback(evt)
        return s

    def run(self):
        """
        Load data and parse data, load resulting Song object into the editor.
        This is a long running task so it will be executed within a worker thread.
        Signals.progress_event will be updated along the way to provide execution
        feedback.
        """ 
        url = self.input_url.text()
        if url.startswith('http'):
            s = self.run_download(url)
        else:
            s = load_midi(url)

        if isinstance(s, Song):
            self.progress.setValue(100)
            self.message_text.setText("")

            if s.title is None or s.title == "":
                p = pathlib.Path(url)
                s.title = p.stem 
            Signals.imported_song.emit(s)
            self.accept()
                     

    def get_data(self):
        return self.input_url.text()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.resize(300, 200)
        
        button = QPushButton("Open Settings Dialog")
        button.clicked.connect(self.open_dialog)
        self.setCentralWidget(button)
        
    def open_dialog(self):
        dialog = ImportDialog(self)
        dialog.show()
        
        # exec() blocks the main loop until the user closes the dialog
        # Check against the fully qualified DialogCode enum
        # if dialog.exec() == QDialog.DialogCode.Accepted:
        #     dialog.run()
        # else:
        #     print("User cancelled the dialog.")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

