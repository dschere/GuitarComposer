#!/usr/bin/env python3
"""
The track editor uses a QGraphicsScene that can manage a massive number
of graphics items effeciently. The track is represented as follows

<staff containing 'traditional' music notation>
<tabature allowing for any instrument to appear as a guitar>
<effects controls that can be turned on or off>
"""

import sys
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt

from common.dispatch import DispatchTable, TOPIC_TABEDITOR_KEY_EVENT 
from ui.editor.keyinput import KeyInputHandler
from ui.editor.tablature import Tablature        

class TabeditorView(QGraphicsView):
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # create viewport
        self.scene.setSceneRect(0, 0, 800, 600)

        # handle/interpret key events  
        self.key_handler = KeyInputHandler()


    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)

        # draw background staff, tablature and effects


    def drawForeground(self, painter: QPainter, rect):
        super().drawForeground(painter, rect)
        
        # draw tab numbers, notes and effect indicators
        
    def keyPressEvent(self, event):
        self.key_handler.key_press_event(event.key())
        
    def focusInEvent(self, event):
        print("Widget gained focus")

    def focusOutEvent(self, event):
        print("Widget lost focus")        

        
    
def unittest():
    app = QApplication(sys.argv)
    view = TabeditorView()
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    unittest()




