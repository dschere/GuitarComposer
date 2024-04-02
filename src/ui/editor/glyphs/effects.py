import os
import sys


from PyQt6.QtWidgets import QApplication, QVBoxLayout, QCheckBox, QPushButton, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

from .canvas import *


module_path = os.path.dirname(__file__)
GearIconEnabledPath  = module_path + os.sep + "data" + os.sep + "Gear-icon-enabled.png"
GearIconDisabledPath = module_path + os.sep + "data" + os.sep + "Gear-icon-disabled.png"




class EffectsGlyph(QPushButton):
    """ 
    shows a gear icon that allows for a dialog to 
      edit details of the effects filter chain.
    """


    width = 50
    height = 50

    def __init__(self, state=None):
        super().__init__()
        self.state = state
        self.enabled_icon = QIcon(GearIconEnabledPath)
        self.disabled_icon = QIcon(GearIconDisabledPath)
        self.initUI()
    
    def initUI(self):

        if self.state:
            icon = self.enabled_icon
        else:
            print(GearIconDisabledPath)
            icon = self.disabled_icon

        self.setIcon(icon)  # Replace "icon2.png" with your icon path
        self.setIconSize(icon.actualSize(QSize(self.width, self.height))) 
        self.setFixedSize(self.width, self.height)
        
        self.clicked.connect(self.settings_dialog) 

    def settings_dialog(self):
        """
        Bring up dialog. 
        if user sets enabled button in dialog then the icon will change
        and state data will be setup. If the icon is disabled then state 
        will be set to disabled. 
        """
        






