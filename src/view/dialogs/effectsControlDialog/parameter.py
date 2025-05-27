"""
Each effect parameter is presented as a row in a QGridLayout.

Effect Name    slider    text-edit   default|value-last-saved.


Editing the text-edit adjusts the value in the slider
Moving the slider updates the text-edit. The signals are 
disconnected/connected between these widgets to prevent 
infinite event loops.

The value is saved prior to the apply button being
clicked. This is the value that is restored by clicking
value-last-saved
"""
from PyQt6.QtWidgets import QWidget, QSlider, QLabel, QPushButton,\
    QGridLayout, QCheckBox, QLineEdit, QApplication, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from models.effect import Effect
from models.param import EffectParameter
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QIcon


NAME_COL    = 0
BOOL_COL    = 1
RANGE_COL   = 1
TEXT_COL    = 2
DEF_COL     = 3
REV_COL     = 4

        
class ParameterRow(QObject):
    def _set_default_btn_css(self, ep: EffectParameter):
        css = ""
        if ep.current_value != ep.default_value:
            css = "QPushButton { background-color: red; }"
        self.default_button.setStyleSheet(css)
        self.default_button.update()

    def _setup_literal(self, grid: QGridLayout, row: int, ep: EffectParameter):
        lit_value = QLineEdit()
        if ep.pres_type == ep.UNBOUNDED_INTEGER:
            dv = QIntValidator()
            lit_value.setValidator(dv)
            lit_value.setText(str(int(ep.current_value)))
            
            d : QPushButton = self.default_button
            r : QPushButton = self.revert_button

            d.clicked.connect(lambda : lit_value.setText(str(int(ep.default_value))))
            r.clicked.connect(lambda : lit_value.setText(str(int(self.original_value))))

        else:
            dv = QDoubleValidator()
            lit_value.setValidator(dv)
            lit_value.setText(str(ep.current_value))
            d : QPushButton = self.default_button
            r : QPushButton = self.revert_button
            
            d.clicked.connect(lambda : lit_value.setText(str(ep.default_value)))
            r.clicked.connect(lambda : lit_value.setText(str(self.original_value)))

        def lit_value_changed(text):
            v = float(text)
            ep.current_value = v
            self._set_default_btn_css(ep)

        grid.addWidget(lit_value, row, TEXT_COL)
        lit_value.textChanged.connect(lit_value_changed)

    def _setup_boolean(self, grid: QGridLayout, row: int, ep: EffectParameter):
        bool_value_ctrl = QCheckBox()
        bool_value_ctrl.setChecked({
            1.0: True,
            0.0: False
        }.get(self.original_value,False))

        def on_value_change(*args):
            v = 1.0 if bool_value_ctrl.isChecked() else 0.0
            ep.current_value = v 
            self._set_default_btn_css(ep) 

        # setup style for default button.
        self._set_default_btn_css(ep)

        bool_value_ctrl.clicked.connect(on_value_change)
        grid.addWidget(bool_value_ctrl, row, BOOL_COL)   


    def _setup_bounded(self, grid: QGridLayout, row: int, ep: EffectParameter):
        """ 
        <slider>|<text entry>
        """
        slider_value_ctrl = QSlider()
        slider_value_ctrl.setOrientation(Qt.Orientation.Horizontal)   
        slider_value_ctrl.setMinimum(0)
        slider_value_ctrl.setMaximum(len(ep.choices)-1)


        literal_value = QLineEdit()
        if ep.is_integer:
            iv = QIntValidator()
            literal_value.setValidator(iv)
            literal_value.setText("%7d" % int(ep.current_value))
        else:
            dv = QDoubleValidator() 
            dv.setDecimals(2)
            literal_value.setValidator(dv)
            literal_value.setText("%4.3f" % ep.current_value)
            
        def nearest_idx(target):
            v = min(ep.choices, key=lambda x: abs(x - target))
            return ep.choices.index(v)

        slider_value_ctrl.setValue(nearest_idx(ep.current_value))

        def slider_value_changed(i: int):
            ep.current_value = ep.choices[i]
            literal_value.textChanged.disconnect(lit_value_changed)
            if ep.is_integer:
                literal_value.setText("%7d" % int(ep.current_value))
            else:
                literal_value.setText("%4.3f" % ep.current_value)
            literal_value.textChanged.connect(lit_value_changed)
            self._set_default_btn_css(ep)

        def lit_value_changed(text):
            try:
                if ep.is_integer:
                    v = int(text)
                else:
                    v = float(text)
            except ValueError:
                return
            i = nearest_idx(v)

            slider_value_ctrl.valueChanged.disconnect(slider_value_changed)
            slider_value_ctrl.setValue(i)
            slider_value_ctrl.valueChanged.connect(slider_value_changed)
            
            ep.current_value = ep.choices[i]
            self._set_default_btn_css(ep)

        self.default_button.clicked.connect(lambda: lit_value_changed(str(ep.default_value)))
        self.revert_button.clicked.connect(lambda: lit_value_changed(str(self.original_value)))

        slider_value_ctrl.valueChanged.connect(slider_value_changed)
        literal_value.textChanged.connect(lit_value_changed)

        grid.addWidget(slider_value_ctrl, row, RANGE_COL)
        grid.addWidget(literal_value, row, TEXT_COL)
        

        
    def __init__(self, grid: QGridLayout, row: int, ep: EffectParameter):
        super().__init__()
        self.original_value = ep.current_value 
        self.value_changed = pyqtSignal(float)
        

        param_name = QLabel()
        param_name.setText(ep.name)

                
        revert_icon = QIcon.fromTheme('document-revert')
        revert_button = QPushButton()
        revert_button.setIcon(revert_icon)
        revert_button.setIconSize(QSize(16, 16))
        revert_button.setToolTip(f"revert value to {self.original_value}")

        default_icon = QIcon.fromTheme('document-new')
        default_button = QPushButton()
        default_button.setIcon(default_icon)
        default_button.setIconSize(QSize(16, 16))
        
        if ep.has_default:  
            default_button.setToolTip(f"revert value to {ep.default_value}")
        else:
            default_button.setDisabled(True)

        self.param_name = param_name
        self.default_button = default_button
        self.revert_button = revert_button

        if ep.pres_type in (ep.BOUNDED_REAL, ep.BOUNDED_INTEGER):
            self._setup_bounded(grid, row, ep) 
        elif ep.pres_type == ep.BOOLEAN:
            self._setup_boolean(grid, row, ep)
        else:
            self._setup_literal(grid, row, ep)

        grid.addWidget(param_name, row, NAME_COL)
        grid.addWidget(self.default_button, row, DEF_COL)
        grid.addWidget(self.revert_button, row, REV_COL)


def unittest():
    import sys 
    from services.effectRepo import EffectRepository

    repo = EffectRepository()
    effect = repo.get('guitarix-distortion')
    plist = effect.getParameters()
    

    app = QApplication(sys.argv)
    container = QWidget()
    grid = QGridLayout()
    container.setLayout(grid)

    container.show()

    for (row, ep) in enumerate(plist):
        ParameterRow(grid, row, ep)

    sys.exit(app.exec()) 



if __name__ == '__main__':
    unittest()
