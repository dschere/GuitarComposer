
import uuid


from PyQt6.QtWidgets import (QDialog, QCheckBox, QVBoxLayout, QComboBox, QLineEdit, QToolBar, QHBoxLayout, QGraphicsView, QGridLayout,
                             QGraphicsScene, QTreeWidget, QTreeWidgetItem, QWidget, QLabel, QSplitter, QMenuBar,
                             QGraphicsPathItem, QMenu, QMessageBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QAction, QPen, QColor, QPainterPath, QTransform

from models.filterGraph import (FilterGraph, GraphNode, InputNode, OutputNode, SplitterNode, 
                                MixerNode, EffectNode, LowPassNode, HighPassNode, 
                                BandPassNode, GainBalanceNode)

from view.dialogs.effectsControlDialog.parameter import ParameterRow
from util.layoutRemoveAllItems import layoutRemoveAllItems

from view.events import Signals

from models.effect import EffectParameter
from services.effectRepo import EffectRepository
from util.midi import midi_codes



class PropertiesPanel(QWidget):

    def _create_freq_control(self, row, label_text, freq, on_change):

        label = QLabel(label_text, self)
        self.content_layout.addWidget(label, row, 0)
        
        freq_edit = QLineEdit(str(freq), self)
        freq_edit.setText(str(freq))
        self.content_layout.addWidget(freq_edit, row, 1)

        note_names = midi_codes.generic_names()
        noteChoices = QComboBox(self)
        noteChoices.addItems(note_names)
        self.content_layout.addWidget(noteChoices, row, 2)

        midi_code = -1

        def freq_edit_change():
            try:
                new_freq = float(freq_edit.text())
            except ValueError: 
                return 
            finally:
                on_change(new_freq, midi_code)

        def note_choices_selected():
            note_name = noteChoices.currentText()
            midi_code = midi_codes.midi_code(note_name)
            new_freq = midi_codes.freq_from_midi_code(midi_code)
            freq_edit.setText("%5.2f" % new_freq)
            on_change(new_freq, midi_code)


        freq_edit.textChanged.connect(freq_edit_change)
        noteChoices.currentIndexChanged.connect(note_choices_selected)
        
    def clear(self):
        layoutRemoveAllItems(self.enabled_layout)
        layoutRemoveAllItems(self.content_layout)
        self.title.setText("Properties")
        

    def __init__(self, parent=None):
        super().__init__(parent)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        self.setMinimumWidth(375)


        self.title = QLabel("Properties")
        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        mainLayout.addWidget(self.title)

        self.enabled_layout = QHBoxLayout()
        self.enabled_layout.setContentsMargins(0, 0, 0, 0)
        self.enabled_layout.setSpacing(0)

        mainLayout.addLayout(self.enabled_layout)
        

        self.content_layout = QGridLayout()
        
        mainLayout.addLayout(self.content_layout)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        mainLayout.addStretch()

        # outer layout is a VBox holding a title
        # and a content area for the parameters.
        # The grid layout is regenerated based on the 
        # graphics item generated. 
        self.setLayout(mainLayout)

        # parameters associated with the current graph node.
        self.parameters : list[EffectParameter] = []

        Signals.graph_node_selected.connect(self.setup)


    # dispatch table for the setup() 
    setup_dispatch = {}

    # SplitterNode
    def setup_splitter(self, gnode: SplitterNode):
        label = QLabel("output ports", self)
        self.content_layout.addWidget(label, 0, 0)

        result_label = QLabel('', self)
        self.content_layout.addWidget(result_label, 0, 1)

        def on_change(value):
            gnode.set_num_out_ports(value)
            result_label.setText(str(value))
            Signals.graph_node_changed.emit(gnode)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(gnode.num_out_ports())
        slider.setMinimum(gnode.MIN_NUM_OUT_PORTS)
        slider.setMaximum(gnode.MAX_NUM_OUT_PORTS)

        slider.setValue(gnode.num_out_ports())
        slider.setSingleStep(1)

        slider.valueChanged.connect(on_change)
        self.content_layout.addWidget(slider, 0, 3)

    setup_dispatch[SplitterNode.__name__] = setup_splitter        

    # MixerNode 
    def setup_mixer(self, gnode: MixerNode):
        n = gnode.num_in_ports()
        if n < gnode.MIN_NUM_IN_PORTS:
            n = gnode.MIN_NUM_IN_PORTS
        if n > gnode.MAX_NUM_IN_PORTS:
            n = gnode.MAX_NUM_IN_PORTS

        label = QLabel("input ports", self)
        self.content_layout.addWidget(label, 0, 1)

        result_label = QLabel(str(n), self)
        self.content_layout.addWidget(result_label, 0, 2)

        def on_change(value):
            gnode.set_num_in_ports(value)
            result_label.setText(str(value))
            Signals.graph_node_changed.emit(gnode)

        slider = QSlider(Qt.Orientation.Horizontal)

        slider.setValue(n)
        slider.setMinimum(gnode.MIN_NUM_IN_PORTS)
        slider.setMaximum(gnode.MAX_NUM_IN_PORTS)

        slider.setValue(gnode.num_in_ports())
        slider.setSingleStep(1)

        slider.valueChanged.connect(on_change)
        self.content_layout.addWidget(slider, 0, 3)

    setup_dispatch[MixerNode.__name__] = setup_mixer

    def setup_lowpass(self, gnode: LowPassNode):
        def on_change(threshold, midi_code_threshold):
            gnode.threshold = threshold
            gnode.midi_code_threshold = midi_code_threshold
            Signals.graph_node_changed.emit(gnode)

        self._create_freq_control(0, "Cutoff Frequency", gnode.threshold, on_change)

    setup_dispatch[LowPassNode.__name__] = setup_lowpass


    def setup_gainbalance(self, gnode: GainBalanceNode):
        gain_label = QLabel("gain", self)
        self.content_layout.addWidget(gain_label, 0, 0)

        gain_slider = QSlider(Qt.Orientation.Horizontal)
        # multiplier value for samples from the range of 0-2.0 with a default value of 1.0        
        gain_slider.setValue(int(gnode.gain * 100))
        gain_slider.setMinimum(0)
        gain_slider.setMaximum(200)
        self.content_layout.addWidget(gain_slider, 0, 1)

        gain_value = QLabel()
        gain_value.setText("%" +  "%3d" % int(gnode.gain * 100))
        self.content_layout.addWidget(gain_value, 0, 2)              

        def on_gain_change(value):
            gnode.gain = value * 0.01
            gain_value.setText("%" +  "%3d" % value)
            Signals.graph_node_changed.emit(gnode)
        gain_slider.valueChanged.connect(on_gain_change)



        # balance is -1.0 to 1.0 representing all left to all right on the speaker

        balance_label = QLabel("balance", self)
        self.content_layout.addWidget(balance_label, 1, 0)

        balance_slider = QSlider(Qt.Orientation.Horizontal)
        balance_slider.setValue(int(gnode.balance * 100))
        balance_slider.setMinimum(-100)
        balance_slider.setMaximum(100)
        self.content_layout.addWidget(balance_slider, 1, 1)


        def on_balance_change(value):
            gnode.balance = int(value / 100.0)
            Signals.graph_node_changed.emit(gnode)
        balance_slider.valueChanged.connect(on_balance_change)



    setup_dispatch[GainBalanceNode.__name__] = setup_gainbalance


    def setup_highpass(self, gnode: HighPassNode):
        def on_change(threshold, midi_code_threshold):
            gnode.threshold = threshold
            gnode.midi_code_threshold = midi_code_threshold

        self._create_freq_control(0, "Cutoff Frequency", gnode.threshold, on_change)

    setup_dispatch[HighPassNode.__name__] = setup_highpass

    def setup_bandpass(self, gnode: BandPassNode):
        def on_low_change(threshold, midi_code_threshold):
            gnode.low_threshold = threshold
            gnode.low_midi_code_threshold = midi_code_threshold

        def on_high_change(threshold, midi_code_threshold):
            gnode.high_threshold = threshold
            gnode.high_midi_code_threshold = midi_code_threshold

        self._create_freq_control(0, "Low Frequency", gnode.low_threshold, on_low_change)
        self._create_freq_control(1, "High Frequency", gnode.high_threshold, on_high_change)

    setup_dispatch[BandPassNode.__name__] = setup_bandpass

    def setup_effect(self, gnode: EffectNode):
        repo = EffectRepository()
        effect = repo.get(gnode.effect_label)
        self.parameters = effect.getParameters()

        self.enabled_layout.addWidget(QLabel("Enabled", self))
        enabled_checkbox = QCheckBox(self)
        enabled_checkbox.setChecked(gnode.enabled)
        self.enabled_layout.addWidget(enabled_checkbox)
        self.enabled_layout.addStretch()
        enabled_checkbox.clicked.connect(lambda e: gnode.set_enabled(enabled_checkbox.isChecked()))  
            
        class value_binder:
            def __init__(self, er, pname):
                self.er = er
                self.pname = pname

            def __call__(self, value):
                #print(f"setting {self.pname} to {value}")
                gnode.properties[self.pname] = value


        for (row, ep) in enumerate(self.parameters):
            if ep.name not in gnode.properties:
                gnode.properties[ep.name] = ep.default_value
            else:
                ep.current_value = gnode.properties[ep.name]

            er = ParameterRow(self.content_layout, row, ep)
            #print(f"{ep.name} {ep.current_value} {ep.default_value}")
            er.value_changed.connect(value_binder(er, ep.name))

    setup_dispatch[EffectNode.__name__] = setup_effect


    def setup(self, gnode: GraphNode):
        """
        Update content based on new graphics node. Wire changes
        based on ui to generate the properties data in the graph node.
        """
        key = gnode.__class__.__name__
        if key in self.setup_dispatch:
            # erase content 
            self.clear()
            self.title.setText(f"{gnode.label()} properties")
            self.setup_dispatch[key](self, gnode)
        

def unittest():
    import sys
    from PyQt6.QtWidgets import QApplication
    import qdarktheme

    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    window = PropertiesPanel()


    gnode = MixerNode()
    window.setup(gnode)

    #gnode = BandPassNode()
    #window.setup(gnode)

    # effect = EffectNode()
    # effect.effect_path = "/usr/lib/ladspa/tap_reverb.so"
    # effect.effect_label = "tap_reverb"
    # window.setup(effect)
    


    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    unittest()
