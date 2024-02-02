import time

from PyQt6.QtCore import QTimer

from common.dispatch import TOPIC_TABEDITOR_KEY_EVENT, DispatchTable, TabEditKeyEvent

KEY_RIGHT_ARROW=16777236
KEY_LEFT_ARROW=16777234
KEY_UP_ARROW=16777235
KEY_DOWN_ARROW=16777237
KEY_TAB=16777217
KEY_SHIFT=16777218
KEY_SPACE=32

# twice the twitch rate
MAX_AGE = 0.44 


class KeyEvent:
    def __init__(self, key):
        self.key = key
        self.timestamp = time.time()
        
    def isDigit(self):
        return self.key >= 48 and self.key <= 57  
        
    def isDynamic(self):
        try:
            return chr(self.key).lower() in ["m","f","p"]    
        except ValueError:
            return False
        
    def asDynamic(self):
        return chr(self.key).lower()    
        
    def asDigit(self):
        return self.key - 48    
        
        

class KeyInputHandler:
    def __init__(self):
        self.key_queue = []
        self.triplet = False
        
    def getFretNumber(self, digit):
        fnum = None
        
        while len(digit) > 2:
            del digit[0:2]
            
        if len(digit) == 2:
            fnum = digit[0] * 10 + digit[1]
        elif digit == 1:
            fnum = digit[0]    
        
        return fnum
        
    def proc_keys(self):
        # clean all keys that are too old.
        v = time.time() - MAX_AGE
        self.key_queue = \
            list(filter(lambda ke: ke.timestamp > v, self.key_queue))
        
        digit = []
        dynamic = []
        shift = False
        tab = False
        left = False
        right = False
        up = False
        down = False
        rest = False
        duration = None
        
        
        print([x.key for x in self.key_queue])
        
        for ke in self.key_queue:
            if ke.isDigit():
                digit.append(ke.asDigit())
            elif ke.isDynamic():
                dynamic.append(ke.asDynamic())    
            elif ke.key == KEY_SHIFT:
                shift = True
            elif ke.key == KEY_TAB:
                tab = True         
            elif ke.key == KEY_RIGHT_ARROW:
                right = True
            elif ke.key == KEY_LEFT_ARROW:
                left = True
            elif ke.key == KEY_UP_ARROW:
                up = True
            elif ke.key == KEY_DOWN_ARROW:
                down = True
            elif ke.key == KEY_SPACE:    
                rest = True    
            else:
                try:
                    ch = chr(ke.key).lower()
                except:
                    ch = ''    
                if ch == 'q': duration = 1
                if ch == 'h': duration = 2
                if ch == 'w': duration = 4
                if ch == 'e': duration = 0.5
                if ch == 's': duration = 0.25
                if ch == 'h': duration = 0.125
                if ch == 'i': duration = 0.0625
                if ch == 't': 
                    self.triplet = True if self.triplet == False else False
                
        if self.triplet and duration != None:
            duration *= 0.66
        
        tek = TabEditKeyEvent()
        tek.fretnum = None if len(digit) == 0 else self.getFretNumber(digit)
        tek.dynamic = None if len(dynamic) == 0 else "".join(dynamic)[:3]
        tek.right = right
        tek.left = left
        tek.up = up
        tek.down = down
        tek.tab = tab
        tek.rest = rest
        tek.duration = duration
        tek.triplet = self.triplet
        
        # publish keyboard event
        DispatchTable.publish(TOPIC_TABEDITOR_KEY_EVENT, None, tek)
        
                     
    def key_press_event(self, key):
        self.key_queue.append( KeyEvent(key) )
        self.proc_keys()
        
        
