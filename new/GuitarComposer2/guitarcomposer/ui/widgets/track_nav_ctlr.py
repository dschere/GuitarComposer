""" 
<add track>
Grid of the following
  <delete>, <track name>, <instrument>, <time sig>, dots for each measure 
  
"""

from PyQt6.QtWidgets import (QApplication, QStyle, QWidget, 
    QListWidget, QListWidgetItem, QHBoxLayout, 
    QFrame, QVBoxLayout, QLabel, QPushButton)

from guitarcomposer.common import midi_instrument_codes
from guitarcomposer.ui.model.track import track



class NavTrackControllerIface:
    def delete_track(self, track_name):
        pass

    def add_track(self, track_model):
        pass

    def get_track_models(self):
        pass
        


class NavTrackWidget(QWidget):
     def __init__(self, controller):
         super().__init__()
         self.controller = controller
         self.layout = QGridLayout()

         self.initUI()
         
     def initUI(self):
         # Button to add a track.    






"""

class NavTrackItem(QWidget):
    
    def add_delete_button(self):
        # trash icon to delete a track
        del_btn = QPushButton()
        pixmapi = QStyle.StandardPixmap.SP_TrashIcon
        icon = self.style().standardIcon(pixmapi) 
        del_btn.setIcon(icon)
        del_btn.setToolTip("delete track")
        del_btn.clicked.connect(controller.delete_track(self.tname))
        return del_btn 
    
    def __init__(self, controller, tname, instrument, timesig):
        super().__init__()
        self.tname = tname
        self.instrument = instrument 
        self.timesig = timesig
        self.controller = controller
        
        layout = QVBoxLayout()
        layout.addWidget(self.add_delete_button())
        
        
        

class NavTrackWidget(QWidget):
    def __init__(self, track_name, instrument_name, parent=None):
        super().__init__(parent)
        self.track_name = track_name
        self.instrument_name = instrument_name
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        # Display track name and instrument name
        label_text = f"{self.track_name} - {self.instrument_name}"
        label = QLabel(label_text)
        layout.addWidget(label)

        def handler(i):
            print("%s box %d clicked" % (self.track_name,i))

        # Display visualization boxes
        for i in range(16):
            box = QFrame()
            
            box.setFixedSize(8, 8)
            box.setStyleSheet("background-color: white; border: 1px solid black;")
            box.mousePressEvent = lambda event, index=i: handler(index)
            layout.addWidget(box)

        self.setLayout(layout)
        
"""
