from models.effect import Effect, Effects
from models.param import EffectParameter
from view.dialogs.effectsControlDialog.parameter import ParameterRow

from services.effectRepo import EffectRepository

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QGridLayout, 
        QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
        QCheckBox, QLabel, QPushButton, QSpacerItem, QSizePolicy)
from typing import Dict, List, Tuple
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont


EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]

class EffectPreview:
    def __init__(self, e :Effects, c: EffectChanges):
        self.effects = e
        self.changes = c
        self.note = "C3"
        self.repeat_note = False
        self.note_interval = 120        



class EffectsDialog(QDialog):
    effect_repo = EffectRepository()

    # user wishes to preview the effects
    effect_preview = pyqtSignal(EffectPreview)
    # user wishes to update the current effects state in the
    # track.
    effect_updated = pyqtSignal(Effects)
    selected_effect : Effect | None  = None

    # allow for enabled effects to be displayed in
    # bold text.
    effect_list_model = QStandardItemModel()
    effect_item_table : Dict[str,QStandardItem] = {}

    def is_filtered(self, text):
        """
        return true|false if the text entered in filter text box
        is contained within text. the search is case insensitive.
        if the filter text is blank then the filter is disabled. 
        """
        ft : QLineEdit = self.effect_name_filter
        t = ft.text().lower()
        if t == "":
            return False
        return text.lower().find(t) == -1 
    
    def populate_effect_name_combo(self):
        """
        Repopulate the the values in teh effect combo box, allow
        the user to filter the list.
        """
        self.effect_list_model.clear()
        enames = self.effects.get_names()
        enames.sort()

        for n in enames:
            item = QStandardItem(n)
            e = self.effects.get_effect(n)
            assert(e)
            font = QFont()
            font.setBold(e.is_enabled())
            item.setFont(font)
            self.effect_list_model.appendRow(item)
            self.effect_item_table[n] = item

        self.effect_name_combo.setModel(self.effect_list_model)
        


    def clear_grid_layout(self):
        layout : QGridLayout = self.param_grid
        while layout.count():
            item = layout.takeAt(0)
            if not item:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def on_enabled_change(self):
        state = self.enable_ctrl.isChecked()
        layout : QGridLayout = self.param_grid
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.setEnabled(state)
            
        n = self.effect_name_combo.currentText()
        e = self.effects.get_effect(n)
        assert(e)
        #item = self.effect_item_table[n]
        e.enabled = state
        idx = self.effect_name_combo.currentIndex() 
        item = self.effect_list_model.item(idx)
        font = item.font()
        font.setBold(e.is_enabled())
        item.setFont(font)

        self.effect_name_combo.update()
            

    def on_effect_selected(self):
        n = self.effect_name_combo.currentText()
        e = self.effects.get_effect(n)
        assert(e)
        
        self.enable_ctrl.setChecked(e.is_enabled())
        # clear grid
        self.clear_grid_layout()
        # repopulate
        plist = e.getParameters()
        for (row, ep) in enumerate(plist):
            ParameterRow(self.param_grid, row, ep)
        # set enable/disable
        self.on_enabled_change()  


    def setup_effect_select_row(self, layout : QVBoxLayout):
        ctrl_row_layout = QGridLayout()

        self.effect_name_filter_lbl = QLabel("filter: ")
        self.effect_name_filter = QLineEdit()
        self.effect_name_combo = QComboBox()

        ctrl_row_layout.addWidget(self.effect_name_filter_lbl, 0, 0)
        ctrl_row_layout.addWidget(self.effect_name_filter, 0, 1)
        ctrl_row_layout.addWidget(self.effect_name_combo, 1, 1)

        self.effect_name_combo.setMaxVisibleItems(10)
        self.populate_effect_name_combo()

        self.effect_name_combo.currentIndexChanged.connect(self.on_effect_selected)

        layout.addLayout(ctrl_row_layout) 

    

    def on_preview(self):
        #evt = EffectPreview(self.effects, self.delta()) 
        #self.effect_preview.emit(evt)
        pass

    def on_apply(self):
        pass

    def setup_control_row(self, layout : QVBoxLayout):
        """
        setup row with enable disable button.
        """
        ctrl_layout = QHBoxLayout()

        self.enable_ctrl = QCheckBox()
        self.enable_ctrl.setText("Enable: ")
        self.preview_effect = QPushButton()
        self.preview_effect.setToolTip("preview these effect settings")
        self.apply_effect = QPushButton()
        self.apply_effect.setToolTip("assign effect settings to track or moment in track.")

        self.preview_effect.clicked.connect(self.on_preview)
        self.apply_effect.clicked.connect(self.on_apply)

        ctrl_layout.addWidget(self.enable_ctrl)
        spacer = QSpacerItem(40, 20)
        ctrl_layout.addSpacerItem(spacer)
        ctrl_layout.addWidget(self.preview_effect)
        ctrl_layout.addWidget(self.apply_effect)

        self.enable_ctrl.clicked.connect(self.on_enabled_change)

        layout.addLayout(ctrl_layout)
        


    def __init__(self, parent=None, effects: Effects | None = None):
        super().__init__(parent)
        self.setWindowTitle("Audio Effects Control")
        self.effects = effects if effects else self.effect_repo.create_effects()

        layout = QVBoxLayout()
        self.param_grid = QGridLayout()

        self.setLayout(layout)

        # effect select row
        self.setup_effect_select_row(layout)

        # effect control row
        self.setup_control_row(layout)

        # effect paramters row
        placeholder = QLabel("Please select an effect from the menu")
        self.param_grid.addWidget(placeholder, 0, 0)

        layout.addLayout(self.param_grid)
         



def unittest():
    import sys
    from models.note import Note
    from PyQt6.QtWidgets import QApplication
    from services.synth.synthservice import synthservice
    from music.instrument import Instrument, getInstrumentList
    import qdarktheme


    SynthService = synthservice()
    SynthService.start()

    from models.effect import Effects
    #import gcsynth
    #import copy 

    # data = {"sfpaths": [
    #     "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
    # gcsynth.start(copy.deepcopy(data))
    
    

    def pretty_print(params):
        for p in params.values():
            print(vars(p))

    ilist = getInstrumentList()
    instr = Instrument(ilist[0])

    app = QApplication(sys.argv)
    dialog = EffectsDialog(None)

    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)


    def on_preview(evt : EffectPreview):
        #  synth, chan, ec: EffectChanges ):
        instr.update_effect_changes(SynthService,0,evt.changes)
        n = Note()
        n.string = 4
        n.fret = 0
        n.velocity = 100
        n.duration = 2000
        instr.note_event(n)

    dialog.effect_preview.connect(on_preview)

    dialog.exec()
    SynthService.stop()


if __name__ == '__main__':
    unittest()


