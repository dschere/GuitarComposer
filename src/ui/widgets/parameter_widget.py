"""
Depending on the data type of the parameter, the widget will
show either a slider, a checkbox, a combobox of text or a text
entry. 
"""


from PyQt6.QtWidgets import QPushButton, QCheckBox, \
    QSlider, QLabel, QHBoxLayout, QTextEdit, QWidget
from PyQt6.QtCore import Qt


from models.param import Parameter, BoolParam, IntParam, FloatParam
from common.dispatch import DispatchTable


class ParameterWidget(QWidget):
    
    def _setup_bool_param(self, layout, topic, param):
        """
        boolean paramter: This is just a text box
        """
        checkbox = QCheckBox(param.name,self)
        checkbox.setChecked(param.value)
        
        def state_change(state):
            checked = False
            if state == 2: # 2 means checked
                checked = True            
                 
            data = { 'value': checked } 
            DispatchTable.publish(topic, checkbox, data)
        
        checkbox.stateChanged.connect(state_change)
        
        reset = QPushButton("reset", self)
        reset.setFixedWidth(50)
        reset.clicked.connect(lambda *args: \
            checkbox.setChecked(param.defval)) 

        layout.addWidget(reset)        
        layout.addWidget(checkbox)
        
    def _setup_int_param(self, layout, topic, param):
        """
        For an integer parameter a slider is used with a min/max 
        range, along with an edit widget that shows what the value is
        and allows for the slider to be updated if it is edited.
        """
        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider.setMinimum(param.minval)
        slider.setMaximum(param.maxval)

        value_editor = QTextEdit(self)
        value_editor.setFixedHeight(30)
        value_editor.setFixedWidth(50)
        value_editor.setText( str(param.value) )
        
        slider.setValue( param.value )
        
        def on_slider_change(value):
            # update text no signals to avoid race condition
            value_editor.blockSignals(True)   
            value_editor.setText(str(value))
            value_editor.blockSignals(False)   
            
            DispatchTable.publish(topic, slider, {'value':value})
            
        def on_editor_change(*args):
            text = value_editor.toPlainText()
            if len(text) > 0:
                value = int(text)
                if param.minval <= value <= param.maxval:
                    slider.setValue(value)
                
        slider.valueChanged.connect(on_slider_change)
        value_editor.textChanged.connect(on_editor_change)        


        reset = QPushButton("reset", self)
        reset.setFixedWidth(50)
        reset.clicked.connect(lambda *args: \
            slider.setValue(param.defval)) 

        layout.addWidget(reset)
        layout.addWidget(slider)
        layout.addWidget(value_editor)
         
        
    def _setup_float_param(self, layout, topic, param):
        
        def to_slider_val(val):
            dp = (val - param.minval)/(param.maxval - param.minval)
            return int(dp * 100)
            
        def to_param_val(slider_value):
            dp = slider_value / 100.0
            diff = param.maxval - param.minval
            return param.minval + (dp * diff)    
        
        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider.setMinimum(0)
        slider.setMaximum(100)

        value_editor = QTextEdit()
        value_editor.setFixedHeight(30)
        value_editor.setFixedWidth(50)
        value_editor.setText( str(param.value) )
        
        
        slider_value = to_slider_val(param.value)
        slider.setValue( slider_value )
        
        def on_slider_change(slider_value):
            value = to_param_val(slider_value)
            
            # update text no signals to avoid race condition
            value_editor.blockSignals(True)   
            value_editor.setText(str(value))
            value_editor.blockSignals(False)   
            
            DispatchTable.publish(topic, slider, {'value':value})
            
        def on_editor_change(*args):
            text = value_editor.toPlainText()
            if len(text) > 0:
                value = float(text)
                if param.minval <= value <= param.maxval:
                    slider.setValue(to_slider_val(value))
                
        slider.valueChanged.connect(on_slider_change)
        value_editor.textChanged.connect(on_editor_change)        

        reset = QPushButton("reset", self)
        reset.setFixedWidth(50)
        reset.clicked.connect(lambda *args: \
            slider.setValue(to_slider_val(param.defval)) ) 

        # add widgets to layout        
        layout.addWidget(reset)
        layout.addWidget(slider)
        layout.addWidget(value_editor)
        
    
    def setup(self, topic, param):
        assert( isinstance(param,Parameter) ) 
        
        layout = QHBoxLayout()
                
        if isinstance(param, BoolParam):
            self._setup_bool_param(layout, topic, param)

        elif isinstance(param, IntParam):
            pname = QLabel(param.name, self)
            pname.setMinimumWidth(100) 
            layout.addWidget(pname)
            self._setup_int_param(layout, topic, param)

        elif isinstance(param, FloatParam):
            pname = QLabel(param.name, self)
            pname.setMinimumWidth(100) 
            layout.addWidget(pname)
            self._setup_float_param(layout, topic, param)
        else:
            raise TypeError("Unsupported parameter type" + \
                str(type(param)))

        self.setLayout(layout)
                     

def unittest():
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    main_win = QMainWindow()
    
    layout = QVBoxLayout()
    
    bp = BoolParam( defval=True, name="boolparam" )
    ip = IntParam( defval=5, minval=1, maxval=10, name="intparam" )
    fp = FloatParam( defval=2.5, minval=0.5, maxval=8.5, name="floatparam" )
    
    def handler(topic, obj, data):
        print(topic + " -> " + str(data))    
    DispatchTable.subscribe("bp", handler)
    DispatchTable.subscribe("ip", handler)
    DispatchTable.subscribe("fp", handler)

    p1 = ParameterWidget()
    p1.setup("bp", bp)
    layout.addWidget( p1 )
    
    p2 = ParameterWidget()
    p2.setup("ip", ip)
    layout.addWidget( p2 )
    
    p3 = ParameterWidget()
    p3.setup("fp", fp)
    layout.addWidget( p3 )
    
    central_widget = QWidget()
    central_widget.setLayout(layout)
    main_win.setCentralWidget(central_widget)
    
    main_win.show()
    sys.exit(app.exec())
    
if __name__ == '__main__':
    unittest()    

