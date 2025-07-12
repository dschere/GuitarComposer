from PyQt6.QtWidgets import (QHBoxLayout, QDialogButtonBox,
                             QDialog, QLineEdit, QLabel,
                             QVBoxLayout, QComboBox, QGroupBox, QPushButton)

from music.instrument import getInstrumentList
from view.events import EditorEvent, EffectPreview, Signals, InstrumentSelectedEvent

from view.config import LabelText
from util.midi import midi_codes
from models.track import Track

from view.dialogs.effectsControlDialog.dialog import EffectsDialog


"""
The sub widget that draws a

  <filter instrument list>
  <instrument list combo box>

* able to route an instrument selected to asignal and pass
  along the track associated with this event
* able to filter the instrument list
"""


class TrackTreeDialog(QDialog):
    instrument_names = getInstrumentList()
    title = "Instrument"

    def _filter_instruments(self):
        ftext = self.filter_input.text().lower()
        self.instruments_combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [
            item for item in self.instrument_names if ftext in item.lower()]
        self.instruments_combo_box.addItems(filtered_items)

    def _on_instrument_selected(self):
        evt = InstrumentSelectedEvent()
        evt.instrument = self.instruments_combo_box.currentText()
        evt.track = self.track_model
        self.track_qmodel_item.setText(evt.instrument)
        Signals.instrument_selected.emit(evt)

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
        dialog = EffectsDialog(self, self.track_model.effects)

        def on_preview(evt : EffectPreview):
            Signals.preview_effect.emit(evt)

        dialog.effect_preview.connect(on_preview)
        dialog.show()

    def __init__(self, parent, track_model : Track, track_qmodel_item):
        super().__init__(parent)
        self.setWindowTitle(LabelText.nav_track_properties)
        self.track_model = track_model
        self.track_qmodel_item = track_qmodel_item

        # filtered drop down menu to select an instrument
        main_layout = QVBoxLayout()

        # Create OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)

        # Connect the buttons to the dialog's accept() and reject() slots
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # line 1 is text box that allows the user to search an instrument.
        filter_layout = QHBoxLayout()
        filter_label = QLabel(LabelText.filter_instruments, self)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self._filter_instruments)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)

        # line 2 is a combobox of sorted instruments
        combo_layout = QHBoxLayout()
        combo_label = QLabel(LabelText.instruments, self)
        self.instruments_combo_box = QComboBox(self)
        self.instruments_combo_box.addItems(self.instrument_names)
        self.instruments_combo_box.setCurrentText(
            self.track_model.instrument_name)
        f = self._on_instrument_selected
        self.instruments_combo_box.currentIndexChanged.connect(f)

        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.instruments_combo_box)

        # line 3 tuning
        tuning_box = self.tuning_section()

        effects_btn = QPushButton() 
        effects_btn.setText("Audio Effects")
        effects_btn.clicked.connect(self.launch_effects)

        # add to main layout
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(combo_layout)
        main_layout.addWidget(tuning_box)
        main_layout.addWidget(effects_btn)
        main_layout.addWidget(button_box)
         

        self.setLayout(main_layout)
