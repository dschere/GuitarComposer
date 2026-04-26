"""
This is a toolbar collection that allows for the user to preview the effects
filter for an instrument.

This also provides a test harness for development of gcsynth.
"""
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QToolBar, QComboBox
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize


from models.filterGraph import FilterGraph
from services.synth.fgraph_agent import FilterGraphAgent
from view.widgets.instrumentPicker import instrumentPicker
from music.instrument import Instrument
from models.note import Note

from util.gctimer import GcTimer





class FGPreviewToolbar(QToolBar):
    def __init__(self, model: FilterGraph):
        super().__init__()
        self.instrument_name = "Steel Guitar"
        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setToolTip("Filter Graph Preview")

        self.setIconSize(QSize(16, 16))

        action = QAction("Preview", self)
        action.triggered.connect(self.on_preview)
        action.setEnabled(False)
        self.preview_action = action
        self.addAction(action)

        ip = instrumentPicker(self.instrument_name)
        ip.instrument_selected.connect(self.on_inst_selected)
        
        self.addWidget(ip)

        self.error_label = QLabel()
        self.addWidget(self.error_label)


        self.model = model

    def set_model(self, model: FilterGraph):
        self.model = model

    def enable_preview(self):
        self.preview_action.setEnabled(True)

    def disable_preview(self):
        self.preview_action.setEnabled(False)

    def set_errmsg(self, text):
        self.error_label.setText(text)

    def on_preview(self):
        intr = Instrument(self.instrument_name) 
            
        
        self.model.pretty_print()
        fga = FilterGraphAgent(self.model)

        for chan in intr.get_channels_used():
            fga.assign_to_channel(chan)

        def unasign_fg(fga):
            print(f"unassign {fga}")
            for chan in intr.get_channels_used():
                fga.unassign_from_channel(chan)
            self.enable_preview()
            del fga


        def note_test(c=60):
            n = Note() 
            n.midi_code = c 
            n.string = 1
            n.fret = 0
            n.velocity = 80 
            n.duration = 2.0

            self.disable_preview()
            intr.note_event(n)

            t = GcTimer()
            tid = t.start(n.duration, unasign_fg, (fga,))
            
        note_test()
    

    def on_inst_selected(self, name):
        self.instrument_name = name




