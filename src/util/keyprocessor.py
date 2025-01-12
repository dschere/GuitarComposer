from PyQt6.QtCore import Qt

from models.track import TabEvent
from view.config import EditorKeyMap

from music import dynamic



class KeyProcessor:
    def __init__(self):
        self._buffer = []
        self._buf_maxlen = 3

    def fret_value(self, key, te: TabEvent):
        if key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9: 
            if te.fret[te.string] == 1:
                te.fret[te.string] = 10 + key - Qt.Key.Key_0
            elif te.fret[te.string] == 2:
                te.fret[te.string] = 20 + key - Qt.Key.Key_0
                if te.fret[te.string] > 24:
                    te.fret[te.string] = 24
            else:
                te.fret[te.string] = key - Qt.Key.Key_0
        elif key in (Qt.Key.Key_Space, Qt.Key.Key_Delete):
            te.fret[te.string] = -1
 

    FFF = [ord('f'),ord('f'),ord('f')]
    FF  = [ord('f'),ord('f')]
    F   = [ord('f')]
    MF  = [ord('m'),ord('f')]
    MP  = [ord('m'),ord('p')]
    PPP = [ord('p'),ord('p'),ord('p')]
    PP  = [ord('p'),ord('p')]
    P   = [ord('p')]

    def proc_dynamic(self, key: int, te: TabEvent):
        if key not in [ord('f'),ord('m'),ord('p')]:
            self._buffer = []
            return False
        
        if len(self._buffer) == 0:
            if key == ord('p'):
                te.dynamic = dynamic.P
            elif key == ord('f'):
                te.dynamic = dynamic.F
            self._buffer.append(key)

        elif self._buffer == [ord('m')]:
            if key == ord('p'):
                te.dynamic = dynamic.MP
                self._buffer = self.MP
            elif key == ord('f'):
                te.dynamic = dynamic.MF
                self._buffer = self.MF
            else:
                self._buffer = []
                return self.proc_dynamic(key, te) 

        elif self._buffer in (self.MP,self.MF,self.PPP,self.FFF):
            self._buffer = []
            return self.proc_dynamic(key, te) 


        elif self._buffer == self.F:
            if key == ord('f'):
                self._buffer = self.FF
                te.dynamic = dynamic.FF
            else:
                self._buffer = []
                return self.proc_dynamic(key, te) 

        elif self._buffer == self.FF:
            if key == ord('f'):
                self._buffer = self.FFF
                te.dynamic = dynamic.FFF
            else:
                self._buffer = []
                return self.proc_dynamic(key, te) 

        elif self._buffer == self.P:
            if key == ord('p'):
                self._buffer = self.PP
                te.dynamic = dynamic.PP
            else:
                self._buffer = []
                return self.proc_dynamic(key, te) 

        elif self._buffer == self.PP:
            if key == ord('p'):
                self._buffer = self.PPP
                te.dynamic = dynamic.PPP
            else:
                self._buffer = []
                return self.proc_dynamic(key, te) 

        return True

    def proc(self, key, te: TabEvent):
        km = EditorKeyMap()    

        # see if the key srokes form a dynamic setting
        # fff, ppp mp etc.  
        if self.proc_dynamic(key, te):
            return

        km = EditorKeyMap()
        if key == km.DOTTED_NOTE:
            if te.dotted:
                # toggle 
                te.dotted = False
                te.double_dotted = False
            else:
                te.dotted = True
                te.double_dotted = False
        elif key == km.DOUBLE_DOTTED_NOTE:
            if te.double_dotted:
                # toggle, clear both 
                te.dotted = False
                te.double_dotted = False
            else:
                te.dotted = False
                te.double_dotted = True
        elif key in km.dur_lookup:
            te.duration = km.dur_lookup[key]
        else:
            self.fret_value(key, te)