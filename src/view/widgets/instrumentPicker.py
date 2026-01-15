"""
Allow user to select an instrument grouped by categories or
select/create a custom instrument that is blend of instruments.
"""
import os 

from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout,
    QToolButton, QMenu, QLabel, QLineEdit
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from view.widgets.svgLabel import SvgLabel
from PyQt6.QtWidgets import QSizePolicy

from music.instrument import getInstrumentGroups

from PyQt6.QtCore import pyqtSignal

class instrumentPicker(QWidget):
    instrument_selected = pyqtSignal(str)
    percussion_selected = pyqtSignal(bool)


    def on_selected(self, action):
        ins_name = action.text()
        self.tool_button.setText(ins_name)
        self.instrument_selected.emit(ins_name)
        self.percussion_selected.emit(ins_name in self.drum_kits)

    def setup_menu(self, filter_text = None ):
        insGroups, customIns = getInstrumentGroups()  

        self.menu.clear()
        groupNames = list(insGroups.keys())
        groupNames.sort()
        for groupName in groupNames:
            ilist = insGroups[groupName]
            sub = self.menu.addMenu(groupName)
            for ins_name in ilist:
                if filter_text is None or filter_text.lower() in ins_name.lower():
                    sub.addAction(ins_name) # type: ignore
                    if groupName == "drums":
                        self.drum_kits.add(ins_name)

        sub = self.menu.addMenu("Custom")
        for cname in customIns:
            if filter_text is None or filter_text.lower() in ins_name.lower():
                sub.addAction(cname) # type: ignore 

    def _filter_instruments(self):
        ftext = self.filter_instrument_name.text().lower()
        self.setup_menu(ftext)

    def __init__(self, currentSelection: str, gridLayout = None, **opts):
        super().__init__()
        self.drum_kits = set()
        self.currentSelection = currentSelection
                
        #self.setMaximumWidth(300)
        
        if gridLayout is None:
            _layout = QGridLayout()
        else:
            _layout = gridLayout
        _layout.setSpacing(0)


        if opts.get('enable_filter',False):
            label = SvgLabel()
            label.setSvgImage(SvgLabel.FILTER_SVG)
            label.setToolTip("filter instruments")
            self.filter_instrument_name = QLineEdit()
            self.filter_instrument_name.setPlaceholderText("filter instruments ...")
            self.filter_instrument_name.textChanged.connect(self._filter_instruments)


            _layout.addWidget(label, 0, 0)
            _layout.addWidget(self.filter_instrument_name, 0, 1)


        button = QToolButton()

        button.setMaximumWidth(150)
        button.setText(currentSelection)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setStyleSheet("""
            QToolButton::menu-indicator {
                top: -5px;     /* fine-tune vertical offset */
                left: -5px;
            }
            QToolButton {
                border: 1px solid gray;    /* flat look */
                padding: 5px;
            }
            QToolButton:hover {
                border: 3px solid gray; /* outline on hover */
                border-radius: 3px;
            }
            """
        )


        self.tool_button = button

        self.menu = QMenu(button)
        self.menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.menu.setSizePolicy(size_policy)

        self.setup_menu()
        self.menu.triggered.connect(self.on_selected)    
        button.setMenu(self.menu)

        # below is a menu
        _layout.addWidget(button, 1, 1)
        self.setLayout(_layout)


