"""
This module renders music engraving such as notes, rests, staff
and time signatures.

    
Column1
    
   |
   | --> flag

   x/o --> note head
   .. --> if a chord multiple not heads
   
Column2

   modifiers
   
   dots
   bend
   stroke
   accents
"""

import math

from PyQt6.QtWidgets import QApplication, QGraphicsLineItem, \
    QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont


WHOLE_NOTE="𝅝 "
HALF_NOTE="𝅗𝅥 "
QUATER_NOTE="𝅘𝅥 "
EIGHT_NOTE="𝅘𝅥𝅮 "
SIXTEENTH_NOTE="𝅘𝅥𝅯 "
THRITYSEC_NOTE="𝅘𝅥𝅰 "
SIXTYFORTH_NOTE="𝅘𝅥𝅱 "

FLAT_SIGN="♭ "
NATURAL_SIGN="♮ "
SHARP_SIGN="♯ "

BARLINE1="𝄀 "
BARLINE2="𝄁 "
END_REPEAT="𝄂 "
START_REPEAT="𝄃 "


TREBLE_CLEFF="𝄞 "
DRUM_CLEFF="𝄥 "
BASS_CLEFF="𝄢 "

WHOLE_REST="𝄻 "
HALF_REST="𝄼 "
QUATER_REST="𝄽 "
EIGHTH_REST="𝄾 "
SIXTEENTH_REST="𝄿 "
THRITYSEC_REST="𝅀 "
SIXTYFORTH_REST="𝅁 "

GHOST_NOTEHEAD="𝅃 "


SymFontSize = {
    FLAT_SIGN: 16,
    SHARP_SIGN: 16,
    NATURAL_SIGN: 16,
    TREBLE_CLEFF: 48,
    DRUM_CLEFF: 48,
    BASS_CLEFF: 48
}
DEFAULT_SYM_FONT_SIZE = 32

class Gylph:
    
    def add_sign(self, scene, sym, x, y):
        size = SymFontSize[sym]
        sign = QGraphicsTextItem(sym)
        font = QFont("DejaVu Sans", size)  # font with good Unicode support
        sign.setFont(font)
        sign.setPos(x, y)
        sign.setZValue(2)
        scene.addItem(sign)

    def bounds(self):
        w = self.bounding_rect.width()
        h = self.bounding_rect.height()
        return w, h
    
    def __init__(self, scene, sym, x, y, **opts):
        # Set the font with Unicode support
        def_size = SymFontSize.get(sym,DEFAULT_SYM_FONT_SIZE)
        size = opts.get('size',def_size)

        if opts.get('dot',False):
            sym += '.'

        text_item = QGraphicsTextItem(sym)

        font = QFont("DejaVu Sans", size)  # font with good Unicode support
        text_item.setFont(font)
        text_item.setPos(x, y)  

        # Add the text item to the scene
        scene.addItem(text_item)       
        
        self.bounding_rect = text_item.boundingRect()
      
        
        if opts.get("line",False):
            line = QGraphicsLineItem(x,y+size+10,x+25,y+size+10)
            line.setZValue(1)
            scene.addItem(line)
        else:
            self.line = None

        if opts.get("flat",False):
            self.add_sign(scene,FLAT_SIGN, x, y)
        elif opts.get("natural",False):
            self.add_sign(scene,NATURAL_SIGN, x, y)
        elif opts.get("sharp",False):
            self.add_sign(scene,SHARP_SIGN, x, y)
                
                
                
                
"""        
class TabeditorView(QGraphicsView):
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # create viewport
        self.scene.setSceneRect(0, 0, 800, 600)        
"""   
        
def unittest():
    import sys
    
    app = QApplication(sys.argv)
    view = QGraphicsView()
    scene = QGraphicsScene()

    # Create a rectangle item
    #rect_item = QGraphicsRectItem(0, 0, 100, 100)

    symList = [WHOLE_NOTE,HALF_NOTE,QUATER_NOTE,EIGHT_NOTE,\
        SIXTEENTH_NOTE,THRITYSEC_NOTE,SIXTYFORTH_NOTE,FLAT_SIGN,\
        NATURAL_SIGN,SHARP_SIGN,BARLINE1,BARLINE2,END_REPEAT,\
        START_REPEAT,TREBLE_CLEFF,DRUM_CLEFF,BASS_CLEFF,WHOLE_REST,\
        HALF_REST,QUATER_REST,EIGHTH_REST,SIXTEENTH_REST,\
        THRITYSEC_REST,SIXTYFORTH_REST,GHOST_NOTEHEAD]
    for (i,sym) in enumerate(symList):
        x = i * 50
        y = 80
        if i < 4:
            g = Gylph(scene, sym, x, y, line=True, dot=True, natural=True)
        else:    
            g = Gylph(scene, sym, x, y)
        print(g.bounds())
    
    view.setScene(scene)
    view.show()

    # Make the rect_item accessible in CustomGraphicsView
    #view.rect_item = text_item

    sys.exit(app.exec())
            

if __name__ == '__main__':
    unittest()


