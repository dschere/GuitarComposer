"""
Each string in a custom instrument is made of a collection of
stringComponents which are an instrument and wweighting. So a 
string could hypothetically be made of a harp (60%) and nylon string
guitar (40%).

This module presents this as a instrument picket and silder. It reuses
the ParameterRow class from the effectsControlDialog module to present
the slider and text-edit for the weighting of the instrument in the string.

"""

from PyQt6.QtWidgets import (QSlider, QDialog, QWidget, QSlider, QGridLayout,QApplication,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QListWidget, QComboBox, QToolBar, QMainWindow, QGridLayout,
                             QStyle, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

from guitar_composer.models.effect import EffectParameter
from guitar_composer.view.dialogs.effectsControlDialog.parameter import ParameterRow, NAME_COL, REV_COL   
from guitar_composer.view.dialogs.customInstrument.models import custom_instrument_string_list_item_spec

def replace_widget(layout: QGridLayout, row: int, col: int, new_widget: QWidget):
    item = layout.itemAtPosition(row, col)

    if item is not None:
        old_widget = item.widget()
        if old_widget is not None:
            layout.removeWidget(old_widget)
            old_widget.deleteLater()

    layout.addWidget(new_widget, row, col)


class stringComponent(QWidget):
    """
    Each string can be implemented by multiple instruments with weighting factor that controls
    value. This object implements the view for a single row. 
    """
    
    def __init__(self, spec: custom_instrument_string_list_item_spec):
        """ 
        Modified parameter widget, use a instrument picket for the parameter name label
        """
        from guitar_composer.view.widgets.instrumentPicker import instrumentPicker
        super().__init__()

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        row = 0 

        self.spec = spec
        # spoof a float ladsp parameter with a range between 0-1.0 this widget
        # contains a slider and a reset button and text bix that can change the 
        # slider when the number is altered.
        self.p = EffectParameter({
            "default_value": spec.weight,
            "is_bounded_above": True,
            "lower_bound": 0.0,
            "is_bounded_below": True,
            "upper_bound": 1.0,
            "current_value": spec.weight,
            "original_value": spec.weight,
            "name": spec.instrument_name,
            "pres_type": EffectParameter.BOUNDED_REAL    
        })
        
        # almost what we need but replace the paramter name label with 
        # an instrument picker 
        pr = ParameterRow(grid, row, self.p)
        # capture value change event.
        pr.value_changed.connect(lambda v: spec.set_weight(v))

        instrument_picker = instrumentPicker(spec.instrument_name,
                parent=self, has_custom_instruments=False)
        instrument_picker.instrument_selected.connect(lambda name: spec.set_name(name))
        
        # replace the QLabel (normally the parameter name) with the instrument picker widget
        replace_widget(grid, row, NAME_COL, instrument_picker)

        # add a trash icon button to the end of the row.
        delete_col = REV_COL+1

        self.delete_button = QPushButton()
        css = "QPushButton { background-color: red; }"
        self.delete_button.setStyleSheet(css)
        self.delete_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))  # type: ignore
        self.delete_button.setToolTip("Delete instrument")
        grid.addWidget(self.delete_button, row, delete_col)

        self.setLayout(grid)

    def set_delete_handler(self, function):
        def on_clicked():
            reply = QMessageBox.question(
                None,
                "Confirmation",
                "Delete instrument?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No # Default button
            )
            if reply == QMessageBox.StandardButton.Yes:
                function(self)
        self.delete_button.clicked.connect(on_clicked)


    


