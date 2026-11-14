
import sys
import json
from typing import List

from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtWidgets import (QSlider, QDialog, QWidget, QSlider,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
                             QListWidget, QComboBox, QToolBar, QMainWindow, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QAction, QIcon
from singleton_decorator import singleton

from guitar_composer.view.widgets import instrumentPicker

from .customIntstrumentContent import customInstrumentContent
from .models import custom_instrument_spec



class CustomInstrumentDialog(QDialog):
    INSTRUMENT_SPACER = "<select>"

    # Events 

    def evt_select_triggered(self, instrument_name):
        if instrument_name != self.INSTRUMENT_SPACER:
            data_dict = self.custom_instrument.getSpec(instrument_name)
            spec = custom_instrument_spec()
            spec.setup_from_dict(instrument_name, data_dict)
            self.draft_instrument = spec
            central_widget = customInstrumentContent(self, spec)
            self.main_window_container.setCentralWidget(central_widget)
            
    def evt_new_triggered(self):
        new_instrument = custom_instrument_spec()
        new_instrument.setup_new_instrument()

        self.draft_instrument = new_instrument
        
        central_widget = customInstrumentContent(self, new_instrument)
        self.main_window_container.setCentralWidget(central_widget)

    def evt_close_triggered(self):
        pass 

    def evt_save_triggered(self):
        if self.draft_instrument:
            if self.draft_instrument.name in self.custom_instrument.getNames():
                reply = QMessageBox.question(
                    None,
                    "Confirmation",
                    f"Are you sure you want to overwrite {self.draft_instrument.name}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No # Default button
                )        
                if reply == QMessageBox.StandardButton.No:
                    return
            data = self.custom_instrument.getData()
            self.draft_instrument.add_to_dictionary(data)
            self.custom_instrument.setData(data)
            self.update_instrument_combobox()    

    def evt_delete_triggered(self):
        if self.draft_instrument:        
            reply = QMessageBox.question(
                None,
                "Confirmation",
                f"Are you sure you want to delete {self.draft_instrument.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No # Default button
            )        
            if reply == QMessageBox.StandardButton.No:
                return
            data = self.custom_instrument.getData()
            if self.draft_instrument.name in data:
                del data[self.draft_instrument.name]
                self.custom_instrument.setData(data)
                self.update_instrument_combobox()
    

    # Toolbar Creation

    def create_instrument_name_combobox(self):
        """
        Create a QComboBox populated with the names of available instruments from the CustomInstruments singleton.
        """
        combo_box = QComboBox(self)
        instrument_names = [self.INSTRUMENT_SPACER] + self.custom_instrument.getNames()
        combo_box.addItems(instrument_names)
        combo_box.currentTextChanged.connect(self.evt_select_triggered)
        return combo_box

    def update_instrument_combobox(self):
        self.combo_box.currentTextChanged.disconnect(self.evt_select_triggered)
        self.combo_box.clear()
        instrument_names = [self.INSTRUMENT_SPACER] + self.custom_instrument.getNames()
        self.combo_box.addItems(instrument_names)
        self.combo_box.currentTextChanged.connect(self.evt_select_triggered)

    def create_toolbar(self) -> QToolBar:
        # 1. Create the QToolBar instance
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))  # Set standard icon sizing

        new_icon = QIcon.fromTheme("document-new")

        new_action = QAction(new_icon, "[+]", self)
        new_action.setToolTip("Create a new instrument")
        new_action.triggered.connect(self.evt_new_triggered)

        self.combo_box = self.create_instrument_name_combobox()

        save_icon = QIcon.fromTheme('document-save')
        save_action = QAction(save_icon, "save", self)
        save_action.setToolTip("Save or create instrument")
        save_action.triggered.connect(self.evt_save_triggered)

        delete_btn = QPushButton()
        delete_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)) # type: ignore
        delete_btn.setToolTip("Delete")
        delete_btn.clicked.connect(self.evt_delete_triggered)

        toolbar.addAction(new_action)
        toolbar.addWidget(self.combo_box)
        toolbar.addSeparator()
        toolbar.addAction(save_action)
        toolbar.addWidget(delete_btn)

        return toolbar

    # Constructor

    def __init__(self, parent=None):
        super().__init__(parent)

        self.draft_instrument = None
        self.setWindowTitle("Custom Instrument Dialog")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(768)

        # Invoke singleton instance of CustomInstruments to manage the collection of custom instruments
        from guitar_composer.music.instrument import CustomInstruments, Instrument
        from guitar_composer.view.widgets.instrumentPicker import instrumentPicker


        self.custom_instrument = CustomInstruments()

        top_layout = QVBoxLayout()

        self.main_window_container = QMainWindow()
        self.main_window_container.setCentralWidget(QWidget())  # Set a central widget to avoid warnings

        toolbar = self.create_toolbar()
        self.main_window_container.addToolBar(toolbar)

        top_layout.addWidget(self.main_window_container)
        self.setLayout(top_layout)
































# class InstrumentBlendRow(QWidget):
#     """
#     This widget represents a single row in the StringInstrumentBlend widget. It consists of a QSlider to adjust the weight of the instrument, 
#     a QLabel to display the instrument name, and a QPushButton to remove the row from the selection.

#     The weight can be adjusted using the slider, and the instrument name is displayed next to it. The remove button allows the user to remove the instrument from the selection.
#     """

#     def __init__(self, parent,weighting=50, instrumentName="12-strGT"):
#         super().__init__(parent)

#         layout = QHBoxLayout(self)

        
#         self.weighting_ctrl = QSlider(Qt.Orientation.Horizontal)
#         self.weighting_ctrl.setMinimum(0)
#         self.weighting_ctrl.setMaximum(100)
#         self.weighting_ctrl.setValue(weighting)

#         self.instrument_picker = instrumentPicker(instrumentName, parent=self)

#         delete_btn = QPushButton()
#         delete_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)) # type: ignore
#         delete_btn.setToolTip("Delete")

#         layout.addWidget(self.weighting_ctrl)
#         layout.addWidget(self.instrument_picker)
#         layout.addWidget(delete_btn)

#         self.setLayout(layout)



# class _CustomInstrumentDialog(QDialog):
#     """
#     This dialog is a configurable list of instruments with a weighting factor for each instrument. It allows the user to select multiple instruments 
#     and assign a weight to each, which can be used to create a blended sound from the selected instruments.

#     The widget consists of a list of available instruments, a list of selected instruments with their weights, and buttons to add or remove instruments from the selection.
#     along with a toolbar to add an instrument. 

#     Each row is a qslider, an instrument name and list to choose form and a garbage can to remove 
#     row.  

#     <toolbar>
#        <select>
#        <new>
#        <delete>
#        <preview instrument>
#     </toolbar>
#     <strings>
#       <string name="e"><plus sign to add row>
#          <InstrumentBlendRow/>
#          <InstrumentBlendRow/>
#       ...   
#     </string>
#     """

#     def evt_instrument_selected(self, instrument_name):
#         spec = self.custom_instrument.getSpec(instrument_name)
#         if spec:
#             print(f"Selected instrument: {instrument_name}, Spec: {spec}")

#     def create_instrument_name_combobox(self):
#         """
#         Create a QComboBox populated with the names of available instruments from the CustomInstruments singleton.
#         """
#         combo_box = QComboBox(self)
#         instrument_names = self.custom_instrument.getNames()
#         combo_box.addItem("")
#         for iname in instrument_names:
#             combo_box.addItem(instrument_names)
#         combo_box.currentTextChanged.connect(self.evt_instrument_selected)
#         return combo_box


#     def create_toolbar(self) -> QToolBar:
#         # 1. Create the QToolBar instance
#         toolbar = QToolBar("Main Toolbar")
#         toolbar.setIconSize(QSize(24, 24))  # Set standard icon sizing


#         combo_box = self.create_instrument_name_combobox()
#         toolbar.addWidget(combo_box)


#         # 2. Define the Actions with fallback system theme icons
#         # Syntax: QIcon.fromTheme("standard-theme-name", QIcon("path/to/local/icon.png"))
#         new_icon = QIcon.fromTheme("document-new")
#         open_icon = QIcon.fromTheme("document-open")
#         save_icon = QIcon.fromTheme("document-save")
#         close_icon = QIcon.fromTheme("window-close")
#         delete_icon = QIcon.fromTheme("edit-delete")

#         # 3. Create QActions and connect them to their respective functions
#         self.new_action = QAction(new_icon, "&New", self)
#         self.new_action.setToolTip("Create a new file")
#         self.new_action.triggered.connect(self.on_new_triggered)

#         self.open_action = QAction(open_icon, "&Open", self)
#         self.open_action.setToolTip("Open an existing file")
#         self.open_action.triggered.connect(self.on_open_triggered)

#         self.save_action = QAction(save_icon, "&Save", self)
#         self.save_action.setToolTip("Save the current file")
#         self.save_action.triggered.connect(self.on_save_triggered)

#         self.close_action = QAction(close_icon, "&Close", self)
#         self.close_action.setToolTip("Close the application")
#         self.close_action.triggered.connect(self.on_close_triggered)  

#         self.delete_action = QAction(delete_icon, "&Delete", self)
#         self.delete_action.setToolTip("Delete the selection")
#         self.delete_action.triggered.connect(self.on_delete_triggered)

#         # 4. Populate the toolbar with actions and structural dividers
#         toolbar.addAction(self.new_action)
#         toolbar.addAction(self.open_action)
#         toolbar.addAction(self.save_action)

#         # Add a logical visual separator between file management and destructive actions
#         toolbar.addSeparator()

#         toolbar.addAction(self.delete_action)
#         toolbar.addAction(self.close_action)

#         return toolbar

#     # --- Slot Functions ---
#     def on_new_triggered(self):
#         print("New action triggered.")

#     def on_open_triggered(self):
#         print("Open action triggered.")

#     def on_save_triggered(self):
#         print("Save action triggered.")

#     def on_delete_triggered(self):
#         print("Delete action triggered.")

#     def on_close_triggered(self):
#         print("Close action triggered.")


#     def __init__(self, parent=None):
#         super().__init__(parent)

#         # Invoke singleton instance of CustomInstruments to manage the collection of custom instruments
#         self.custom_instrument = CustomInstruments()


#         self.setWindowTitle("Custom Instrument Dialog")
#         self.setMinimumWidth(1024)
#         self.setMinimumHeight(768)

#         top_layout = QVBoxLayout()
        


#         toolbar = self.create_toolbar()
#         main_window_container = QMainWindow()
#         main_window_container.setCentralWidget(QWidget())  # Set a central widget to avoid warnings
#         main_window_container.addToolBar(toolbar)
        
        
#         top_layout.addWidget(main_window_container)
#         self.setLayout(top_layout)


# def showCustomInstrumentDialog():
#     """
#     This function creates and displays the CustomInstrumentDialog. It initializes the dialog, sets its title, and executes it modally.
#     """
#     from guitar_composer.view.dialogs.customInstrument.stringComponent import unittest

#     unittest()

#     #dialog = CustomInstrumentDialog()
            
#     #dialog.exec()

