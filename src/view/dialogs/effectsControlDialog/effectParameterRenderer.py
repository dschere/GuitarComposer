from PyQt6.QtWidgets import QWidget, QSlider, QLabel, QPushButton,\
    QGridLayout, QCheckBox, QLineEdit, QApplication, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal
from models.effect import Effect
from models.param import EffectParameter
from PyQt6.QtGui import QDoubleValidator, QIntValidator

class ValueControlMixin:
    param_changed = pyqtSignal(EffectParameter)


class CheckboxValueControl(QCheckBox, ValueControlMixin):
    """ 
    This is a boolean parameter.

    Use a QCheckbox for the visual.
    """
    def set_param_value(self, v : bool):
        self.setChecked(v) 
        if v:
            self._param.current_value = 1.0 
        else:
            self._param.current_value = 0.0
        self.param_changed.emit(self._param)
          
    def _on_state_change(self, state):
        if state == 2:
            self._param.current_value = 1.0
        else:
            self._param.current_value = 0.0
        self.param_changed.emit(self._param)

    def __init__(self, param: EffectParameter):
        super().__init__() 

        if int(param.current_value) == 0:
            self.setChecked(False)
        else:
            self.setChecked(True)
        self._param = param
        self.stateChanged.connect(self._on_state_change)
        #self.changeEvent.connect(self._toggle_value)

    def set_default_value(self):
        checked = int(self._param.default_value) != 0
        self.set_param_value(checked)
        


class SliderValueControl(QSlider, ValueControlMixin):
    """ 
    creates a horizontal slider for controling the parameter value,
    a callback is used to tranlate the value to an actual value
    then call a provided callback for rendering the value next to the slider.
    """

    def _on_value_change(self, i: int):
        v = self._param.choices[i]
        self._param.current_value = v
        self.pval_changed(v)
        self.param_changed.emit(self._param)

    def __init__(self, param: EffectParameter, pval_changed):
        super().__init__() 
        self.setOrientation(Qt.Orientation.Horizontal)
        self.pval_changed = pval_changed
        self._param = param 

        self.setMinimum(0)
        self.setMaximum(len(param.choices)-1)

        i = param.choices.index(param.current_value)
        self.setValue(i)

        self.valueChanged.connect(self._on_value_change)
        pval_changed(param.current_value)
        
    def set_default_value(self):
        self.set_param_value(self._param.default_value) 
        
    def set_param_value(self, v: float | int):
        i = self._param.choices.index(v) 
        self.setValue(i)
        self._param.current_value = v 
        self.param_changed.emit(self._param)


class UnboundedRealValueControl(QLineEdit, ValueControlMixin):
    def _on_change(self, text):
        v = float(text)
        self._param.current_value = v
        self.param_changed.emit(self._param)

    def __init__(self, param: EffectParameter):
        super().__init__()
        dv = QDoubleValidator() 
        dv.setDecimals(2)
        self.setValidator(dv)
        self._param = param 
        self.textChanged.connect(self._on_change)

    def set_default_value(self):
        self.set_param_value(self._param.default_value)

    def set_param_value(self, v: float):
        self.setText("%2.2f" % v) 
        self._param.current_value = v
        self.param_changed.emit(self._param)

class UnboundedIntValueControl(QLineEdit, ValueControlMixin):
    def _on_change(self, text):
        v = float(text)
        self._param.current_value = v
        self.param_changed.emit(self._param)

    def __init__(self, param: EffectParameter):
        super().__init__()
        dv = QIntValidator()
        self.setValidator(dv)
        self._param = param 
        self.textChanged.connect(self._on_change)

    def set_default_value(self):
        self.set_param_value(int(self._param.default_value))

    def set_param_value(self, v: int):
        self.setText("%d" % v) 
        self._param.current_value = v
        self.param_changed.emit(self._param)



class EffectParameterRenderer:

    def update_value_indicator(self, v):
        if self.param.is_integer:
            self.value_display.setText("%d" % int(v))
        else:
            self.value_display.setText("%2.2f" % float(v))

    def on_param_changed(self, param: EffectParameter):
        if param.current_value != param.default_value:
            self.reset_default_value_w.setStyleSheet("background-color: red;")
        else:
            self.reset_default_value_w.setStyleSheet("")


    def __init__(self, param: EffectParameter, layout: QGridLayout, row: int):
        self.param = param 

        name_widget = QLabel() 
        name_widget.setText(self.param.name)

        reset_default_value_w = QPushButton() 
        reset_default_value_w.setText("default") 
        reset_default_value_w.setToolTip("reset default value")

        layout.addWidget(name_widget, row, 0)
        layout.addWidget(reset_default_value_w, row, 3)

        if self.param.pres_type == EffectParameter.BOOLEAN:
            self.control = CheckboxValueControl(param)
            layout.addWidget(self.control, row, 1) 
            
        elif self.param.pres_type in (EffectParameter.BOUNDED_REAL,
                                      EffectParameter.BOUNDED_INTEGER):
            self.value_display = QLineEdit() 
            self.control = SliderValueControl(param, self.update_value_indicator)

            dv = QDoubleValidator() 
            dv.setDecimals(2)
            self.value_display.setValidator(dv)
        
            layout.addWidget(self.control, row, 1) 
            layout.addWidget(self.value_display, row, 2) 

        elif self.param.pres_type == EffectParameter.UNBOUNDED_INTEGER:
            self.control = UnboundedIntValueControl(param) 
            layout.addWidget(self.control, row, 1)

        elif self.param.pres_type == EffectParameter.UNBOUNDED_REAL:
            self.control = UnboundedRealValueControl(param) 
            layout.addWidget(self.control, row, 1)

        else:
            raise TypeError(f"Unknown presentation type {self.param.pres_type}")    
        
        reset_default_value_w.clicked.connect(lambda *args: self.control.set_default_value())
        self.reset_default_value_w = reset_default_value_w 
        self.on_param_changed(param) 
        self.control.param_changed.connect(self.on_param_changed)

def unittest():
    from models.effect import Effects
    import gcsynth
    import copy 

    data = {"sfpaths": [
        "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
    gcsynth.start(copy.deepcopy(data))
    
    e = Effects() 

    def pretty_print(params):
        for p in params.values():
            print(vars(p))

    for eff in e.etable.values():
        eff.enable()

    #e.distortion.enable() 
    #e.reverb.enable() 
    #e.chorus_flanger.enable() 

    
    app = QApplication([])
    layout = QGridLayout()
    window = QWidget() 

    for eff in e.etable.values():
        _eff : Effect = eff
        for (row,p) in enumerate(_eff.params.values()):
            EffectParameterRenderer(p, layout, row) 

    window.setLayout(layout)
    window.show()
    app.exec()


if __name__ == '__main__':
    unittest()



    