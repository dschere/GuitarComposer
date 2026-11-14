"""
Generates a note to be played by gcsynth that is used to preview a sound it could 
be an effect preview or custom instrument. The widget presents a choice of notes
and generates an event for the app controller to play.
"""


from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QButtonGroup, QGroupBox,
    QToolButton, QMenu, QLabel, QLineEdit, QComboBox, QHBoxLayout, QStyle)

from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from guitar_composer.view.widgets.svgLabel import SvgLabel
from PyQt6.QtWidgets import QSizePolicy


from PyQt6.QtCore import pyqtSignal

from guitar_composer.view.events import Signals
from guitar_composer.music.instrument import Instrument, StandardTuning
from guitar_composer.models.note import Note 
from guitar_composer.util.midi import midi_codes

class notePreviewer(QWidget):
    will_preview = pyqtSignal()

    def on_selected(self, note_code_selected: str):
        self.note.fret = self.note_choices.index(note_code_selected)
        self.note.midi_code = self.open_string_code + self.note.fret

    def on_preview_clicked(self):
        self.will_preview.emit()
        Signals.preview_play.emit(self.note)

        
    def __init__(self, gstring: int, initial_fret = 0):
        super().__init__()
        self.note = Note()


        # use a standard tuning and the gstring to create a list of notes to play
        # based on fret position.
        open_string = StandardTuning[gstring]
        self.open_string_code = midi_codes.midi_code(open_string)
        self.note_choices = []
        for fret in range(13):
            self.note_choices.append(midi_codes.name(self.open_string_code + fret))

        self.note.string = gstring 
        self.note.fret = initial_fret
        self.note.midi_code = self.open_string_code + initial_fret
        self.note.velocity = 64
        self.note.duration = 1.0
        
        combo = QComboBox()
        combo.addItems(self.note_choices)
        combo.currentTextChanged.connect(self.on_selected)
        combo.setCurrentIndex(initial_fret)
        combo.setToolTip("select note to play")
        
        
        preview_btn = QPushButton() 
        preview_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))  # type: ignore
        preview_btn.setToolTip("preview")
        preview_btn.clicked.connect(self.on_preview_clicked)
        preview_btn.setMaximumWidth(64)
        
        group = QGroupBox("Preview")
        group_layout = QHBoxLayout(group)
        group_layout.setContentsMargins(0,0,0,0)

        group_layout.addStretch()
        group_layout.addWidget(preview_btn)
        group_layout.addWidget(combo)
        group.setMaximumWidth(180)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(group)
        self.setLayout(main_layout)



        
