"""
* creates/updates/deletes audio presets.

A preset is a collection of audio effect settings.

Allow for live audio playing and recording
"""
import sys, os, re    
    
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QScrollArea, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QSizePolicy, QToolBar, QComboBox
from PyQt6.QtWidgets import QStyle, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

# models and data
from models.effect import EffectsSchema, EffectPresets

# specialized widgets
from ui.widgets.parameter_widget import ParameterWidget, ParameterEnableWidget

# messaging
from common.dispatch import DispatchTable,EffectsParamTopic,\
    TOPIC_EFFECTS_RACK_LIVE_START, TOPIC_EFFECTS_RACK_LIVE_STOP
    
        

class EffectsSelectionTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        
        self.setHeaderLabels(["Effects"])
        self.setColumnCount(1)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMaximumSize(16777215, 16777215)  # Set maximum size (2^24 - 1)

        screen = QGuiApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        # Set the dimensions of the dialog
        width = int(screen_rect.width() * 2 / 3) - 50 
        height = int(screen_rect.height() * 2 / 3) - 100

        self.setFixedSize(width,height)


    def setup(self, model):
        # clear existing widgets 
        self.clear()
            
        # effects are organized into groups
        # group +
        #       |
        #       +-- effect 1
        #       +-- effect 2
        # if group only has one effect ...
        # effect <is in the tree position as the group>
        
        for group_name in EffectsSchema["group-order"]:
            elist = EffectsSchema["groups"][group_name]
            effect_tree_item_parent = self
            if len(elist) > 1:
                group_tree_item = QTreeWidgetItem(self)
                group_tree_item.setText(0, group_name)
                effect_tree_item_parent = group_tree_item
                
            for effect_name in elist:         
                effect_tree_item = QTreeWidgetItem(effect_tree_item_parent)
                
                param_e = model.getEnabledParam(effect_name)
                topic = EffectsParamTopic(effect_name,"ENABLED")
                p = ParameterEnableWidget(topic, effect_name, param_e)
                
                effect_tree_item.treeWidget().setItemWidget(effect_tree_item, 0, p)
                
                effects_panel = QTreeWidgetItem(effect_tree_item)
                
                layout = QVBoxLayout()
                for param in model.getParamList(effect_name):
                    topic = EffectsParamTopic(effect_name, param.name)
                    p = ParameterWidget()
                    p.setup(topic, param)
                    layout.addWidget(p)
                
                w = QWidget()
                w.setLayout(layout)    
                effects_panel.treeWidget().setItemWidget(effects_panel, 0, w)    
       
class PlayStopButton(QPushButton):
    """ Controls the play/stop button which will launch an ffmpeg
        instance to capture audio 
    """
    def __init__(self, model, rec_filename, inputDeviceNum):
        super().__init__()
        self.model = model
        self.is_playing = False
        self.setText("Play")
        self.setStyleSheet("background-color: green; color: white;")
        self.clicked.connect(self.toggle)
        self.rec_filename = rec_filename
        self.inputDeviceNum = inputDeviceNum

    def toggle(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            record_filename = self.rec_filename.text()
            msg = {
                   'model': self.model, 
                   'filename': record_filename,
                   'device_number': self.inputDeviceNum()
                }
            DispatchTable.publish(TOPIC_EFFECTS_RACK_LIVE_START,\
                self, 
                msg
            ) 
            self.setText("Stop")
            self.setStyleSheet("background-color: red; color: black;")
        else:            
            DispatchTable.publish(TOPIC_EFFECTS_RACK_LIVE_STOP,\
                self, None) 
            self.setText("Play")
            self.setStyleSheet("background-color: green; color: white;") 
                       
                
                
class PresetsAndPlayControl(QToolBar):
    """
    Preset Control: <divider> <name>   [+][-] 
                              <list of existing>
    """
    
    def delete_preset(self):
        preset = self.preset_select.currentText()
        if self.model.preset_exists(preset):
            buttonReply = QMessageBox.question(self, \
                'Do you really want to delete!', 'Do you want to delete preset?', 
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)        
            if buttonReply == QMessageBox.StandardButton.Yes:
                # removed stored data on disk not the current model.
                self.model.remove(preset)
                self.refresh_preset_combobox()      
    
    def save_model(self):
        preset = self.preset_select.currentText()
        if self.model.preset_exists(preset):
            buttonReply = QMessageBox.question(self, \
                'Preset Exists!', 'Do you want to overwrite existing preset?', 
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)        
            if buttonReply != QMessageBox.StandardButton.Yes:
                return
            
        self.model.save(preset)
        self.refresh_preset_combobox() 
    
    def onPresetSelected(self):
        selected_preset = self.preset_select.currentText()
        # possible to enter a new preset then select the combox
        # so double check that this is a stored preset.
        if selected_preset in self.model.getStoredPresets():
            # load effect settings and refresh controls
            self.model.load(selected_preset)
            self.refresh_settings(self.model)
    
    def refresh_preset_combobox(self):
        self.preset_select.clear()
        preset_names = self.model.getStoredPresets()
        preset_names.sort()
        
        for (i,preset_text) in enumerate(preset_names):
            self.preset_select.insertItem(i,preset_text)
            
    def getDeviceList(self):
        # Use arecord -l to determine input devices for audio capture
        # prefer USB over internal.
        pat = re.compile("card ([0-9])")
        lines = os.popen("arecord -l").readlines()
        
        devlist = []
        for line in lines:
            m = pat.match(line)
            if m:
                card_num = int(m.group(1))
                description = line[m.span()[1]+1:-1]
                isUsb = description.find("USB AUDIO") != -1
                devlist.append({
                    "card": card_num,
                    "desc": description,
                    "isUsb": isUsb
                })
                
                           
        return sorted(devlist, \
            key = lambda item: item['desc'].find('usb') == -1)
            
    def indev_selected(self):
        i = self.indev_select.currentIndex()
        input_device = self.devices[i]['card']
        return input_device
    
    def __init__(self, model, refresh_settings):
        super().__init__()
        self.model = model
        self.refresh_settings = refresh_settings
        
        label = QLabel()
        label.setText("Preset Controls:")
        self.preset_select = QComboBox()
        self.preset_select.setEditable(True)
        self.preset_select.setFixedWidth(200)
        self.preset_select.currentIndexChanged.connect(self.onPresetSelected)

        self.refresh_preset_combobox()        
                    
        save_btn = QPushButton("Save")
        pixmapi = getattr(QStyle.StandardPixmap, "SP_DriveHDIcon")
        icon = self.style().standardIcon(pixmapi)
        save_btn.setIcon(icon)
        save_btn.setStyleSheet("background-color: rgb(0,255,100);")
        save_btn.clicked.connect(self.save_model)

        delete_btn = QPushButton("Delete")
        pixmapi = getattr(QStyle.StandardPixmap, "SP_TrashIcon")
        icon = self.style().standardIcon(pixmapi)
        delete_btn.setIcon(icon)
        delete_btn.setStyleSheet("background-color: rgb(255,0,0);")
        delete_btn.clicked.connect(self.delete_preset)

        rec_label = QLabel()
        rec_label.setText("Record Filename:")
        rec_filename = QLineEdit()
        rec_filename.setFixedWidth(200)
      
        play_toggle_btn = PlayStopButton(self.model, rec_filename, self.indev_selected)
        
        self.devices = self.getDeviceList()
        
        ia_label = QLabel()
        ia_label.setText("Input Audio Device")
        
        indev_select = QComboBox()
        indev_select.setEditable(False)
        for (i,dev) in enumerate(self.devices):
            indev_select.insertItem(i,dev['desc'])
        indev_select.setFixedWidth(200)
        self.indev_select = indev_select
        
        
        # set device default
        self.indev_select.currentIndexChanged.connect(self.indev_selected)

        
        
        self.addWidget(label)
        self.addSeparator()        
        self.addWidget(save_btn)
        self.addWidget(delete_btn)
        self.addWidget(self.preset_select)    
        
        self.addWidget(rec_label)
        self.addWidget(rec_filename)
        self.addWidget(play_toggle_btn)
        self.addWidget(ia_label)
        self.addWidget(indev_select)
        
        
class EffectsRackDialog(QDialog):
    
    def setWindowDimensions(self):
        screen = QGuiApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        # Set the dimensions of the dialog
        dialog_width = int(screen_rect.width() * 2 / 3)
        dialog_height = int(screen_rect.height() * 2 / 3)
        self.setFixedSize(dialog_width, dialog_height) 
    
    def __init__(self):
        super().__init__()
        
        self.model = EffectPresets("default")

        # Create a scroll area
        scroll_area = QScrollArea()
        
        scroll_area.setVerticalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAsNeeded  )  # Set horizontal scroll bar policy

        # Create a widget for the scroll area content
        content_widget = EffectsSelectionTree()
        content_widget.setup(self.model)       
         
        content_layout = QHBoxLayout(content_widget)

        # Set the widget for the scroll area
        scroll_area.setWidget(content_widget)

        preset_control = PresetsAndPlayControl(self.model, content_widget.setup)

        # Create a layout for the dialog
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(preset_control)
        dialog_layout.addWidget(scroll_area)

        self.setLayout(dialog_layout)
        self.setWindowTitle('Effects Rack')
        
        self.setWindowDimensions()
        
# --- unit test code ---- 


class ButtonExample(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create a button
        self.button = QPushButton('Open Dialog', self)

        # Connect the button clicked signal to a slot method
        self.button.clicked.connect(self.onButtonClick)

        self.setGeometry(100, 100, 300, 100)
        self.setWindowTitle('Button Example')
        self.show()

    def onButtonClick(self):
        # Open the scroll dialog
        dialog = EffectsRackDialog()
        dialog.exec()

def unittest():
    app = QApplication(sys.argv)
    ex = ButtonExample()
    sys.exit(app.exec())

if __name__ == '__main__':
    unittest()
