""" 
Controls the live audio capture thread and optional 
effects.
"""
from typing import List
from services.synth.synthservice import synthservice
from view.dialogs.effectsControlDialog.dialog import EffectsDialog

from PyQt6.QtWidgets import (QDialog, QGridLayout, QApplication,
        QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
        QCheckBox, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt
from view.events import LiveCaptureConfig, Signals
from services.usbmonitor import UsbMonitor
from models.effect import Effects
import copy

class LiveEffectsDialog(EffectsDialog):
    """ 
    Modified effects dialog
    """

    def on_apply(self):
        Signals.live_effects.emit(self.all_changes())


    def __init__(self, parent, effects: Effects):
        super().__init__(parent, effects)
        # disable preview
        self.preview_effect.setEnabled(False)
        

class LiveCaptureDialog(QDialog):

    def _on_live_ctrl_clicked(self, state):
        if state == Qt.CheckState.Checked.value:
            evt = LiveCaptureConfig(True, self.deviceListCb.currentText())
            Signals.live_capture.emit(evt)
        elif state == Qt.CheckState.Unchecked.value:
            evt = LiveCaptureConfig(False, self.deviceListCb.currentText())
            Signals.live_capture.emit(evt)

    def _detect_device_list(self):
        synth = synthservice()
        input_devices = synth.list_capture_devices()
        if len(input_devices) == 0:
            self.close()


    effects = Effects()
    
    def _add_effects(self):
        dialog = LiveEffectsDialog(self, self.effects)
        dialog.show()

    def __init__(self, parent, deviceList : List[str]):
        super().__init__(parent)
        layout = QGridLayout()
        

        """
        Device   <drop down of capture devices>
        Live     <start><stop>
        Effects  <effects>
        """
        self.deviceListCb = QComboBox()
        deviceList.sort()
        self.deviceListCb.addItems(deviceList)

        layout.addWidget(QLabel("Device"), 0, 0)
        layout.addWidget(self.deviceListCb, 0, 1)

        self.liveCtrl = QCheckBox()
        self.liveCtrl.setChecked(False)
        self.liveCtrl.stateChanged.connect(self._on_live_ctrl_clicked)

        layout.addWidget(QLabel("Enable"), 1, 0)
        layout.addWidget(self.liveCtrl, 1, 1)

        self.effectCtrl = QPushButton()
        self.effectCtrl.setText("effects")
        self.effectCtrl.clicked.connect(self._add_effects)

        layout.addWidget(self.effectCtrl, 2, 1)

        self.liveCtrl.setStyleSheet("""
            /* Style the checkbox indicator (the square part) */
            QCheckBox::indicator {
                width: 40px;
                height: 40px;
            }
            /* Change the indicator's color to red when unchecked */
            QCheckBox::indicator:unchecked {
                background-color: #FF0000; 
            }
            /* Change the indicator's color to blue when checked */
            QCheckBox::indicator:checked {
                background-color: #0000FF;
            }
            /* Style the checkbox text */
            QCheckBox {
                font-size: 20px;
                color: black;
            }
        """)

        self.setLayout(layout)

        self.usb_monitor = UsbMonitor()
        self.usb_monitor.device_changed.connect(self._detect_device_list)


def unittest():
    import sys, qdarktheme 

    app = QApplication(sys.argv)

    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    ex = LiveCaptureDialog(None, ['PCM2900C Audio CODEC Analog Stereo'])
    ex.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    unittest()        



