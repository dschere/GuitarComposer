import copy

from models.effect import Effect, Effects
from models.param import EffectParameter
from view.dialogs.effectsControlDialog.parameter import ParameterRow

from services.effectRepo import EffectRepository

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QGridLayout, 
        QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
        QCheckBox, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMessageBox)
from typing import Dict, List, Tuple
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont

from view.events import EffectPreview, EffectChanges

class EffectChangeEvent:
    def __init__(self, e: Effects, c: EffectChanges):
        self.effects = e
        self.changes = c


class EffectsDialog(QDialog):
    effect_repo = EffectRepository()

    # user wishes to preview the effects
    effect_preview = pyqtSignal(EffectPreview)
    # user wishes to update the current effects state in the
    # track.
    effect_updated = pyqtSignal(EffectChangeEvent)
    selected_effect : Effect | None  = None

    # allow for enabled effects to be displayed in
    # bold text.
    effect_list_model = QStandardItemModel()
    effect_item_table : Dict[str,QStandardItem] = {}

    effects : Effects | None = None 
    original_effects_state : Effects | None = None


    def is_not_filtered(self, text):
        """
        return true|false if the text entered in filter text box
        is contained within text. the search is case insensitive.
        if the filter text is blank then the filter is disabled. 
        """
        ft : QLineEdit = self.effect_name_filter
        t = ft.text().lower()
        if t == "":
            return True
        return text.lower().find(t) != -1 
    
    def populate_effect_name_combo(self):
        """
        Repopulate the the values in teh effect combo box, allow
        the user to filter the list.
        """
        self.effect_list_model.clear()
        assert(self.effects)
        enames = self.effects.get_names()
        enames.sort()

        for n in enames:
            if self.is_not_filtered(n):
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
        assert(self.effects)
        e = self.effects.get_effect(n)
        if not e:
            return

        #item = self.effect_item_table[n]
        e.enabled = state
        idx = self.effect_name_combo.currentIndex() 
        item = self.effect_list_model.item(idx)
        if item:
            font = item.font()
            font.setBold(e.is_enabled())
            item.setFont(font)

        self.effect_name_combo.setMaxVisibleItems(10)
        self.effect_name_combo.update()
            

    def on_effect_selected(self):
        assert(self.effects)
        n = self.effect_name_combo.currentText()
        e = self.effects.get_effect(n)
        if not e:
            return
        
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
        self.effect_name_filter_lbl.setMaximumWidth(100)
        self.effect_name_filter = QLineEdit()
        self.effect_name_combo = QComboBox()
        self.effect_name_combo.setMaximumWidth(200)
        self.effect_name_filter.setMaximumWidth(200)

        ctrl_row_layout.addWidget(self.effect_name_filter_lbl, 0, 0)
        ctrl_row_layout.addWidget(self.effect_name_filter, 0, 1)
        ctrl_row_layout.addWidget(self.effect_name_combo, 1, 1)

        self.effect_name_combo.setMaxVisibleItems(10)
        
        self.effect_name_combo.setStyleSheet("QComboBox { combobox-popup: 0; }");        

        self.populate_effect_name_combo()

        self.effect_name_combo.currentIndexChanged.connect(self.on_effect_selected)
        self.effect_name_filter.textChanged.connect(self.populate_effect_name_combo)

        layout.addLayout(ctrl_row_layout) 

    def all_changes(self) -> EffectChanges: # type: ignore
        r = {}
        assert(self.effects)

        # in this case were we are not altering a prior effects state then 
        # then simply generate EffectChanges for all enabled effects
        for n in self.effects.get_names():     
            e = self.effects.get_effect(n)
            if e and e.is_enabled():
                r[e] = [(n, e.get_param_by_name(n)) for n in e.getParamNames()]
        return r

    def on_preview(self):
        assert(self.effects)
        evt = EffectPreview(self.effects, self.all_changes()) 
        self.effect_preview.emit(evt)
        
    def on_apply(self):
        # only applicable if we are altering the exising effects state.
        if self.original_effects_state and self.effects:
            reply = QMessageBox.question(
                None,  # parent widget
                "Confirm",  # window title
                "Do you want to apply effect changes?",  # message text
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                e_changes = self.effects.delta(self.original_effects_state) 
                evt = EffectChangeEvent(self.effects, e_changes)
                self.effect_updated.emit(evt)

                self.close()

    def setup_control_row(self, layout : QVBoxLayout):
        """
        setup row with enable disable button.
        """
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(0)
        

        self.enable_ctrl = QCheckBox()
        self.enable_ctrl.setMaximumWidth(100)
        self.enable_ctrl.setText("Enable: ")
        self.preview_effect = QPushButton("preview")
        self.preview_effect.setMaximumWidth(100)
        self.preview_effect.setToolTip("preview these effect settings")
        self.apply_effect = QPushButton("apply")
        self.apply_effect.setMaximumWidth(100)
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
        self.setMinimumWidth(600)

        self.original_effects_state = effects 

        if effects:
            self.effects = copy.deepcopy(effects)
        else:
            self.effects = self.effect_repo.create_effects()
            
        layout = QVBoxLayout()
        layout.setSpacing(0)
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
    import sys, signal
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
        instr.effects_change(evt.changes)
        # send an arbitrary note to hear what applying the effect sounds like.
        n = Note()
        n.string = 4
        n.fret = 0
        n.velocity = 100
        n.duration = 2000
        instr.note_event(n)


    dialog.effect_preview.connect(on_preview)

    dialog.exec()
    SynthService.stop()
    signal.alarm(1)


if __name__ == '__main__':
    unittest()


