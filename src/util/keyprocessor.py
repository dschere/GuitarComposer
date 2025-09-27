from PyQt6.QtCore import Qt

from models.track import TabEvent
from view.config import EditorKeyMap
from view.events import Signals, EditorEvent

from music.constants import Dynamic as dynamic



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
            # If the current tab event is a rest:
            #  determine the duration change and if it fits into
            #  the dur_lookup then alter the structure of the measure
            #  by adding or removing adjacent rests   
            #if te.is_rest():

            d_change = km.dur_lookup[key] - te.duration
            te.duration = km.dur_lookup[key]
            evt = EditorEvent(EditorEvent.REST_DUR_CHANGED)  
            evt.new_dur = km.dur_lookup[key]
            evt.dur_change = d_change
            Signals.editor_event.emit(evt)  

            #else:
            #    te.duration = km.dur_lookup[key]
        elif key == km.TIED_NOTE:
            te.toggle_tied()
        elif key == km.START_REPEAT:
            Signals.editor_event.emit(EditorEvent(EditorEvent.MEASURE_REPEAT_START_KEY))
        elif key == km.END_REPEAT:
            Signals.editor_event.emit(EditorEvent(EditorEvent.MEASURE_REPEAT_END_KEY))
        else:
            self.fret_value(key, te)