"""
This is the widget that makes up the content area of the custom instrument dialog.

here is a layout description 

<toolbar>
   <name of the widget/>
   <spacer>
   <preview that plays a chord>
   <delete>
</toolbar>
<string assignment>
  <high string> <add> <preview>
     <stringComponent/>
     <stringComponent/>
     <stringComponent/>
  <string>
</string assignment>
"""


import sys
import json
from typing import List, cast

from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtWidgets import (QSlider, QDialog, QWidget, QSlider, QMessageBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QListWidget, QComboBox, QToolBar, QMainWindow, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QAction, QIcon
from singleton_decorator import singleton

from .stringComponent import stringComponent
from .models import (custom_instrument_string_spec, 
    custom_instrument_spec, custom_instrument_string_list_item_spec)

from guitar_composer.view.widgets.notePreviewer import notePreviewer
from guitar_composer.music.instrument import Instrument, CustomInstruments, CUSTOM_INSTRUMENT_DRAFT_NAME
from guitar_composer.view.events import Signals

from guitar_composer.view.widgets.accordion import Accordion

from .stringComponent import stringComponent

from guitar_composer.util.gctimer import GcTimer
from guitar_composer.models.note import Note 
from guitar_composer.util.midi import midi_codes
from guitar_composer.music.instrument import StandardTuning


@singleton
class _LocalSignals(QObject):
    note_will_be_previewed = pyqtSignal()
    custom_instrument_updated = pyqtSignal()

    def __init__(self):
        super().__init__() 
LocalSignals = _LocalSignals()

    




class stringAssignment(QWidget):
    """
    Allows user to assign intrument blends on a per string basis.

    This widget shows a list of instrument blends for a given guitar string.
    Provides a means of adding and removing rows. Allows for the ability to preview
    this 
    """

    def add_row(self):
        new_comp = custom_instrument_string_list_item_spec()
        new_comp.instrument_name = Instrument.DEFAULT_PREVIEW_INSTRUMENT
        new_comp.weight = 0.5
        self.spec.components.append(new_comp)

        w = stringComponent(new_comp)
        w.set_delete_handler(self.delete_row)
        self.row_mapping[w] = new_comp
        self.component_layout.addWidget(w)

        LocalSignals.custom_instrument_updated.emit()

    def delete_row(self, w: stringComponent):
        comp = self.row_mapping.get(w)
        if comp in self.spec.components:
            if len(self.spec.components) == 1:
                QMessageBox.warning(self, "Unable to delete", "Must have at least one instrument")
                return
                
            self.component_layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
            
            self.spec.components.remove(comp)
            del self.row_mapping[w]

            LocalSignals.custom_instrument_updated.emit()


    def __init__(self, parent, spec: custom_instrument_string_spec, gstring: int, init_fret: int):
        super().__init__(parent)
        # map a stringComponent to spec.component
        self.row_mapping = {}
        self.spec = spec
        main_layout = QVBoxLayout()
        

        tool_row = QHBoxLayout()
            
        add_btn = QPushButton("+")
        add_btn.setToolTip("Add instrument/weighting to mix")
        css = "QPushButton { background-color: green; }"                     
        add_btn.setStyleSheet(css)
        add_btn.clicked.connect(self.add_row)

        preview = notePreviewer(gstring, init_fret)
        preview.will_preview.connect(lambda : LocalSignals.note_will_be_previewed.emit())
        
        tool_row.addWidget(add_btn)
        tool_row.addStretch()
        tool_row.addWidget(preview)

        main_layout.addLayout(tool_row)

        self.component_layout = QVBoxLayout() 
        for comp in spec.components:
            w = stringComponent(comp)
            w.set_delete_handler(self.delete_row)
            self.row_mapping[w] = comp
            self.component_layout.addWidget(w)
        main_layout.addLayout(self.component_layout)

        self.setLayout(main_layout)            


class stringAssignmentList(QWidget):
    """
    Displays an accordion like structure and allows the user to edit strings
    """
    def __init__(self, parent, spec: custom_instrument_spec):
        super().__init__(parent)
        layout = QVBoxLayout()

        fret_table = [
            0,
            0,
            1,
            2,
            2,
            0
        ]

        self.accordion = Accordion(exclusive=False)
        for (i, string_spec) in enumerate(spec.strings):
            text = f"string {i+1}"
            if i == 0:
                text += " (high E)"
            w = stringAssignment(self, string_spec, i, fret_table[i])
            self.accordion.add_section(text, w)

        layout.addWidget(self.accordion)
        #accordion.setMinimumWidth(1280)
        self.accordion.setMinimumHeight(680)

        LocalSignals.custom_instrument_updated.connect(self.accordion.content_updated)

        self.setLayout(layout)

    def __del__(self):
        LocalSignals.custom_instrument_updated.disconnect(self.accordion.content_updated)


class CustomInstrumentTopRowWidget(QWidget):

    def on_preview_clicked(self):
        "Play an E major cord"
        chord = [
            0,
            0,
            1,
            2,
            2,
            0
        ]
        notes = []
        t = GcTimer()
        for (gstring,fret) in enumerate(chord):
            open_string = StandardTuning[gstring]
            open_string_code = midi_codes.midi_code(open_string)
            note = Note()
            note.string = gstring
            note.fret = fret 
            note.midi_code = open_string_code + fret
            note.velocity = 64
            note.duration = 1.0 
            notes.append(note)

        for n in notes:
            t.start((len(chord) - n.string) * 0.1, Signals.preview_play.emit, (n,)) 

    def on_name_changed(self, text):
        self.spec.name = text

    def __init__(self, parent, spec: custom_instrument_spec):
        super().__init__(parent)
        self.spec = spec
        
        # 
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5) # Optional: Adjust padding as needed

        title_label = QLabel("Name:")

        # 
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Enter text here...")
        self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center the text inside
        self.text_edit.setText(spec.name)
        self.text_edit.textChanged.connect(self.on_name_changed)

        preview_btn = QPushButton() 
        preview_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))  # type: ignore
        preview_btn.setToolTip("preview")
        preview_btn.clicked.connect(self.on_preview_clicked)
        preview_btn.setMaximumWidth(64)

        
        # 3. Create the far-right trash can button
        self.delete_button = QPushButton()
        self.delete_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))  # type: ignore
        self.delete_button.setToolTip("Delete Instrument")
        self.delete_button.setStyleSheet("QPushButton { background-color: red;}")
        
        # 4. Assemble the layout
        # Add stretch *before* the text edit to push it away from the far left if desired.
        # However, to keep the text edit taking up the available space while remaining centered,
        # we add the text edit directly, and the stretch handles its expansion.
        layout.addWidget(title_label)
        layout.addWidget(self.text_edit, stretch=1)
        layout.addWidget(preview_btn) 
        layout.addWidget(self.delete_button)

        self.setLayout(layout)


class customInstrumentContent(QWidget):


    def restore_preview_instrument(self):
        # set the defaualt preview instrument.
        Signals.change_preview_instrument.emit(Instrument.DEFAULT_PREVIEW_INSTRUMENT)

        ci = CustomInstruments()
        ci.clear_draft_data()

    def update_draft_preview_instrument(self):

        # singleton instance, spoof a custom instrument using the model data 
        ci = CustomInstruments()

        # create a draft custom instrument, this is work in progress and will be assigned 
        string_data = []
        for s in self.spec.strings:
            string_weightings = []
            for comp in s.components:
                string_weightings.append((comp.instrument_name, comp.weight))
            string_data.append(string_weightings)
        draft_name = CUSTOM_INSTRUMENT_DRAFT_NAME
        ci.create_draft(draft_name, string_data)        

        # have the app controller change the instrument name to one we are currently working on.
        Signals.change_preview_instrument.emit(CUSTOM_INSTRUMENT_DRAFT_NAME)

    def __del__(self):
        self.restore_preview_instrument()

    def __init__(self, parent, spec: custom_instrument_spec):
        self.spec = spec
        super().__init__(parent)
        layout = QVBoxLayout()

        top_row = CustomInstrumentTopRowWidget(self, spec)
        string_conf = stringAssignmentList(self, spec)

        layout.addWidget(top_row)
        layout.addStretch()
        layout.addWidget(string_conf)

        self.setLayout(layout)        

        self.update_draft_preview_instrument()
        LocalSignals.custom_instrument_updated.connect(self.update_draft_preview_instrument)        
        LocalSignals.note_will_be_previewed.connect(self.update_draft_preview_instrument)

    def __del__(self):
        LocalSignals.custom_instrument_updated.disconnect(self.update_draft_preview_instrument)        
        LocalSignals.note_will_be_previewed.disconnect(self.update_draft_preview_instrument)
