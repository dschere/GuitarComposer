import sys
import copy
from typing import Dict, List, Tuple
import logging


from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QFormLayout, QWidget,
    QCheckBox, QGroupBox, QGridLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal
from models.effect import Effects, Effect
from services.effectRepo import EffectRepository
from models.note import Note
from view.dialogs.effectsControlDialog.effectParameterRenderer import EffectParameterRenderer
from models.param import EffectParameter
from view.dialogs.effectsControlDialog.ladspaSelect import LadspaSelectDialog

EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]

class EffectsTabContent(QWidget):
    def change_enabled(self, state):
        if state:
            self._param_group.setEnabled(True)
            self._effect.enable() 
        else:
            self._param_group.setEnabled(False)
            self._effect.disable() 
        

    def __init__(self, effect: Effect):
        super().__init__()
        main_layout = QVBoxLayout()

        self._effect = effect
        self._enable_button = QCheckBox() 
        self._enable_button.setChecked(effect.is_enabled())
        self._enable_button.setText("Enable: ")
        self._enable_button.clicked.connect(self.change_enabled)
        
        self._param_group = QGroupBox() 
        
        param_layout = QGridLayout() 
        self._param_group.setLayout(param_layout)

        pnames = list(effect.params.keys()) 
        pnames.sort() 
        for (row,pn) in enumerate(pnames):
            ef = effect.params[pn]
            EffectParameterRenderer(ef, param_layout, row)

        main_layout.addWidget(self._enable_button)
        main_layout.addWidget(self._param_group) 

        self.setLayout(main_layout)


class EffectPreview:
    def __init__(self, e :Effects, c: EffectChanges):
        self.effects = e
        self.changes = c
        self.note = "C3"
        self.repeat_note = False
        self.note_interval = 120        

class EffectChangeEvent:
    def __init__(self, e: Effects, c: EffectChanges):
        self.effects = e
        self.changes = c

class EffectsDialog(QDialog):
    effect_repo = EffectRepository()

    effect_preview = pyqtSignal(EffectPreview)
    effect_update = pyqtSignal(EffectChangeEvent)


    def delta(self) -> EffectChanges:
        """ 
        Return a set of parameters for each effect that has been changed.
        """
        r = {}

        def pair(n) -> Tuple[Effect, Effect]:
            a1 = self.effects.etable[n]
            a2 = self.original_effects.etable[n]
            return (a1,a2)
        
        plist = []
        for label in self.effects.etable:
            plist.append(pair(label))
    
        for (e, o) in plist:

            # if we are going from disabled -> enabled then
            # treat all parameters are changed.
            if e.is_enabled() and not o.is_enabled():
                r[e] = list(e.params.items())

            # if we are going from enabled -> disabled then it
            # doesn't matter what the parameters are. the filter
            # is going to be disabled.
            elif not e.is_enabled() and o.is_enabled():
                r[e] = []

            elif e.is_enabled and o.is_enabled():
                diffs = [] 
                for pname in e.params.keys():
                    e_param : EffectParameter = e.params[pname]
                    o_param : EffectParameter = o.params[pname]
                    if e_param.current_value != o_param.current_value:
                        diffs.append((pname,e_param))
                if len(diffs) > 0:
                    r[e] = diffs

            # else disabled -> disabled so do nothing
        if logging.getLogger('root').getEffectiveLevel() == logging.DEBUG:    
            report = "effects\n"
            for e, diffs in r.items():
                report += f"  {e.name} enabled={e.enabled}:\n"
                if e.enabled:
                    for pname, e_param in diffs:
                        report += f"       {e_param}\n"
            logging.debug(report)
        
        return r

    def on_preview(self):
        evt = EffectPreview(self.effects, self.delta()) 
        self.effect_preview.emit(evt)

    def on_update(self):
        evt = EffectChangeEvent(self.effects, self.delta())
        self.effect_update.emit(evt)

    def __init__(self, parent=None, effects: Effects | None = None):
        super().__init__(parent)
        self.setWindowTitle("Audio Effects Control")
        #self.resize(400, 300)

        if not effects:
            self.effects = Effects()
        else:
            self.effects = effects  

        self.original_effects = copy.deepcopy(self.effects)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Create the QTabWidget
        tab_widget = QTabWidget(self)

        data = []
        for label, e in self.effects.etable.items():
            data.append((EffectsTabContent(e), label))

        for (content, name) in data:
            tab_widget.addTab(content, name)

        # Add the tab widget to the main layout
        main_layout.addWidget(tab_widget)

        # control toolbar below
        control_bar = QWidget() 
        control_layout = QHBoxLayout() 
        control_bar.setLayout(control_layout)

        configure = QPushButton("configure")
        configure.clicked.connect(self.on_configure)
        control_layout.addWidget(configure)

        apply = QPushButton("apply")
        apply.clicked.connect(self.on_update)
        control_layout.addWidget(apply)

        preview = QPushButton("preview")
        preview.clicked.connect(self.on_preview)
        control_layout.addWidget(preview)

        main_layout.addWidget(control_bar)

        self.tab_widget = tab_widget

    def on_configure(self):
        dialog = LadspaSelectDialog() 
        # modal dialog that updates the effects repo. 
        dialog.exec()
        self.effect = self.effect_repo.create_effects()

        self.tab_widget.clear()
        data = []
        for label, e in self.effects.etable.items():
            data.append((EffectsTabContent(e), label))

        for (content, name) in data:
            self.tab_widget.addTab(content, name)




def unittest():
    from services.synth.synthservice import synthservice
    from music.instrument import Instrument, getInstrumentList

    SynthService = synthservice()
    SynthService.start()

    from models.effect import Effects
    #import gcsynth
    #import copy 

    # data = {"sfpaths": [
    #     "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
    # gcsynth.start(copy.deepcopy(data))
    
    e = Effects() 

    def pretty_print(params):
        for p in params.values():
            print(vars(p))

    ilist = getInstrumentList()
    instr = Instrument(ilist[0])

    app = QApplication(sys.argv)
    dialog = EffectsDialog(None, e)



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


