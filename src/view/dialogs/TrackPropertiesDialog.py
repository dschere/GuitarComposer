from typing import List, Tuple
from PyQt6.QtWidgets import (QHBoxLayout, QDialogButtonBox,
                             QDialog, QLineEdit, QLabel,QSpinBox,
                             QVBoxLayout, QComboBox, QGroupBox, QPushButton)
from PyQt6.QtCore import Qt

from models.measure import TabEvent
from music.instrument import getInstrumentList
from view.events import EditorEvent, EffectPreview, Signals, InstrumentSelectedEvent

from view.config import LabelText
from util.midi import midi_codes
from models.track import Track
from models.measure import TimeSig

from view.dialogs.effectsControlDialog.dialog import EffectsDialog
from services.effectRepo import EffectRepository

from view.editor.glyphs.common import KEYS

"""
The sub widget that draws a

  <filter instrument list>
  <instrument list combo box>

* able to route an instrument selected to asignal and pass
  along the track associated with this event
* able to filter the instrument list
"""

class TrackPropertiesDialog(QDialog):
    instrument_names = getInstrumentList()
    title = "Instrument"

    def key_list_section(self):
        group_box = QGroupBox(LabelText.keys)
        layout = QVBoxLayout()
        self.key_cb = QComboBox()
        for item in KEYS:
            if isinstance(item,Tuple):
                self.key_cb.addItems(list(item))
            else:
                self.key_cb.addItem(item)

        #key_cb.currentTextChanged.connect(self.update_key)
        self.key_cb.setCurrentText(self.key)
        layout.addWidget(self.key_cb)
        group_box.setLayout(layout)

        return group_box 

    def getTimeSig(self):
        ts = TimeSig()
        ts.beats_per_measure = self.beats_per_bar.value()
        ts.beat_note_id = int(self.beat_type.currentText())
        return ts   
    
    def bpm_section(self):
        group_box = QGroupBox(LabelText.tempo)
        layout = QHBoxLayout()
        
        lbl = QLabel()
        lbl.setText(LabelText.bpm)

        self.bpm_sb = QSpinBox()
        self.bpm_sb.setMinimum(1)
        self.bpm_sb.setMaximum(300)
        self.bpm_sb.setValue(self.bpm)

        layout.addWidget(lbl)
        layout.addWidget(self.bpm_sb)

        group_box.setLayout(layout)
        return group_box
    
    def timesig_section(self):
        group_box = QGroupBox(LabelText.timesig)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.beats_per_bar = QSpinBox()
        self.beats_per_bar.setMinimum(2)
        self.beats_per_bar.setMaximum(64)
        
        lbl = QLabel()
        lbl.setText("________")

        self.beat_type = QComboBox()
        self.beat_type.setFixedWidth(64)
        beat_note_ids = [2,4,8,16]
        self.beat_type.addItems([str(i) for i in beat_note_ids])

        layout.addWidget(self.beats_per_bar, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.beat_type, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.beats_per_bar.setValue( self.ts.beats_per_measure )
        i = beat_note_ids.index(self.ts.beat_note_id)
        self.beat_type.setCurrentIndex(i)

        group_box.setLayout(layout)
        return group_box
         

    def _filter_instruments(self):
        ftext = self.filter_input.text().lower()
        self.instruments_combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [
            item for item in self.instrument_names if ftext in item.lower()]
        self.instruments_combo_box.addItems(filtered_items)
        

    def _on_instrument_selected(self):
        instrument_name = self.instruments_combo_box.currentText()
        self.track_model.instrument_name = instrument_name
        
    def tuning_section(self):
        """ 
        <group line>
        <combo box of common tunings>
        <string #>   <note name> <octave>
        """
        #TODO sync the changes tuning with the keyboard widget 
        
        group_box = QGroupBox(LabelText.tuning)
        layout = QVBoxLayout()

        tuning_preset_cb = QComboBox()
        tuning_data = [
            ("standard",["E4","B3","G3","D3","A2","E2"]),
            ("dadgad",["D4","A3","G3","D3","A2","D2"]),
            ("drop-d",["E4","B3","G3","D3","A2","D2"])
        ]
        tuning_preset_cb.addItems([name for (name,_) in tuning_data])
        def select_tuning(self, idx):
            tuning = tuning_data[idx][1]
            self.track_model.setTuning(tuning)

            evt = EditorEvent()
            evt.ev_type = EditorEvent.TUNING_CHANGE
            evt.tuning = tuning
            Signals.editor_event.emit(evt) 

        tuning_preset_cb.currentIndexChanged.connect(lambda idx: select_tuning(self, idx))

        layout.addWidget(tuning_preset_cb)
        
        
        key_labels = [] 
        for (sharp,flat) in midi_codes.names:
            if sharp == flat:
                key_labels.append(sharp)
            else:
                key_labels.append("%s/%s" % (sharp,flat))
        octive_labels = [str(octave) for octave in range(1,7)]

        group_box.setLayout(layout)
        return group_box
    

    def launch_effects(self):
        er = EffectRepository()
        effects = er.create_effects()
        dialog = EffectsDialog(self, effects)

        def on_preview(evt : EffectPreview):
            Signals.preview_effect.emit(evt)

        dialog.effect_preview.connect(on_preview)
        dialog.show()

    def accept(self, *args):
        super().accept()    

        _, m = self.track_model.current_moment()
        m.key = self.key_cb.currentText()
        m.timesig = self.getTimeSig()
        m.bpm = self.bpm_sb.value()
        self.track_model.instrument_name = self.instruments_combo_box.currentText()

        evt = EditorEvent()
        evt.ev_type = EditorEvent.ADD_MODEL
        evt.model = self.track_model
        Signals.editor_event.emit(evt)

    def reject(self, *args):
        super().reject()    

    def __init__(self, parent, track_model : Track):
        super().__init__(parent)
        self.setWindowTitle(LabelText.nav_track_properties)
        self.track_model = track_model
        #self.track_qmodel_item = track_qmodel_item

        _, m = self.track_model.current_moment()
        self.ts, self.bpm, self.key, self.cleff = track_model.getMeasureParams(m)
        
        # filtered drop down menu to select an instrument
        main_layout = QVBoxLayout()

        # Create OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok )

        # Connect the buttons to the dialog's accept() and reject() slots
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # line 1 is text box that allows the user to search an instrument.
        instr_group_box = QGroupBox(LabelText.instruments)
        instr_group_layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        filter_label = QLabel("filter", self)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self._filter_instruments)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)

        # line 2 is a combobox of sorted instruments
        combo_layout = QHBoxLayout()
        combo_label = QLabel("name", self)
        self.instruments_combo_box = QComboBox(self)
        self.instruments_combo_box.addItems(self.instrument_names)
        self.instruments_combo_box.setCurrentText(
            self.track_model.instrument_name)
        f = self._on_instrument_selected
        self.instruments_combo_box.currentIndexChanged.connect(f)

        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.instruments_combo_box)

        instr_group_layout.addLayout(filter_layout)
        instr_group_layout.addLayout(combo_layout)

        instr_group_box.setLayout(instr_group_layout)

        # line 3 tuning
        tuning_box = self.tuning_section()

        # line 4 key accents
        key_box = self.key_list_section()

        # line 5 time signature
        timesig = self.timesig_section()

        effects_btn = QPushButton() 
        effects_btn.setText("Audio Effects")
        effects_btn.clicked.connect(self.launch_effects)

        # add to main layout
        main_layout.addWidget(instr_group_box)
        main_layout.addWidget(tuning_box)
        main_layout.addWidget(key_box)
        main_layout.addWidget(timesig)
        main_layout.addWidget(self.bpm_section())
        main_layout.addWidget(effects_btn)
        main_layout.addWidget(button_box)  

        self.setLayout(main_layout)
