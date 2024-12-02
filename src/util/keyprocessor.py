from PyQt6.QtCore import Qt

from models.track import TabEvent
from view.config import EditorKeyMap

from music import dynamic



class KeyProcessor:
    def __init__(self):
        self._buffer = []
        self._buf_maxlen = 3

    def fret_value(self, key, tc: TabEvent):
        if key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9: 
            if tc.fret[tc.string] == 1:
                tc.fret[tc.string] = 10 + key - Qt.Key.Key_0
            elif tc.fret[tc.string] == 2:
                tc.fret[tc.string] = 20 + key - Qt.Key.Key_0
                if tc.fret[tc.string] > 24:
                    tc.fret[tc.string] = 24
            else:
                tc.fret[tc.string] = key - Qt.Key.Key_0
        elif key in (Qt.Key.Key_Space, Qt.Key.Key_Delete):
            tc.fret[tc.string] = -1
 

    FFF = [ord('f'),ord('f'),ord('f')]
    FF  = [ord('f'),ord('f')]
    F   = [ord('f')]
    MF  = [ord('m'),ord('f')]
    MP  = [ord('m'),ord('p')]
    PPP = [ord('p'),ord('p'),ord('p')]
    PP  = [ord('p'),ord('p')]
    P   = [ord('p')]

    def proc_dynamic(self, key: int, tc: TabEvent):
        if key not in [ord('f'),ord('m'),ord('p')]:
            self._buffer = []
            return False
        
        if len(self._buffer) == 0:
            if key == ord('p'):
                tc.dynamic = dynamic.P
            elif key == ord('f'):
                tc.dynamic = dynamic.F
            self._buffer.append(key)

        elif self._buffer == [ord('m')]:
            if key == ord('p'):
                tc.dynamic = dynamic.MP
                self._buffer = self.MP
            elif key == ord('f'):
                tc.dynamic = dynamic.MF
                self._buffer = self.MF
            else:
                self._buffer = []
                return self.proc_dynamic(key, tc) 

        elif self._buffer in (self.MP,self.MF,self.PPP,self.FFF):
            self._buffer = []
            return self.proc_dynamic(key, tc) 


        elif self._buffer == self.F:
            if key == ord('f'):
                self._buffer = self.FF
                tc.dynamic = dynamic.FF
            else:
                self._buffer = []
                return self.proc_dynamic(key, tc) 

        elif self._buffer == self.FF:
            if key == ord('f'):
                self._buffer = self.FFF
                tc.dynamic = dynamic.FFF
            else:
                self._buffer = []
                return self.proc_dynamic(key, tc) 

        elif self._buffer == self.P:
            if key == ord('p'):
                self._buffer = self.PP
                tc.dynamic = dynamic.PP
            else:
                self._buffer = []
                return self.proc_dynamic(key, tc) 

        elif self._buffer == self.PP:
            if key == ord('p'):
                self._buffer = self.PPP
                tc.dynamic = dynamic.PPP
            else:
                self._buffer = []
                return self.proc_dynamic(key, tc) 

        return True

    def proc(self, key, tc: TabEvent):
        km = EditorKeyMap()    

        # see if the key srokes form a dynamic setting
        # fff, ppp mp etc.  
        if self.proc_dynamic(key, tc):
            return

        km = EditorKeyMap()
        if key == km.DOTTED_NOTE:
            if tc.dotted:
                # toggle 
                tc.dotted = False
                tc.double_dotted = False
            else:
                tc.dotted = True
                tc.double_dotted = False
        elif key == km.DOUBLE_DOTTED_NOTE:
            if tc.double_dotted:
                # toggle, clear both 
                tc.dotted = False
                tc.double_dotted = False
            else:
                tc.dotted = False
                tc.double_dotted = True
        elif key in km.dur_lookup:
            tc.duration = km.dur_lookup[key]
        else:
            self.fret_value(key, tc)