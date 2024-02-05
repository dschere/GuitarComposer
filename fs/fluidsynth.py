from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from queue import Queue
import atexit

class fluid_synth_dispatcher:
    """
    Helper class containing callback methods. 
    """    
    def noteon(self, chan, key, vel):
        msg = f"noteon {chan} {key} {vel}\n"
        self.s.sendall(msg.encode('utf-8'))
        
    def noteoff(self, chan, key):
        msg = f"noteoff {chan} {key}\n"
        self.s.sendall(msg.encode('utf-8'))
    
    def prog(self, chan, instrument):
        msg = f"prog {chan} {instrument}\n"
        self.s.sendall(msg.encode('utf-8'))

    def pitch_bend_range(self, chan, semitones):
        msg = f"pitch_bend_range {chan} {semitones}\n"
        self.s.sendall(msg.encode('utf-8'))

    def pitch_bend(self, chan, offset):
        msg = f"pitch_bend {chan} {offset}\n"
        self.s.sendall(msg.encode('utf-8'))        
                
    def proc_msg(self, msg):
        #print(msg)
        f = self.dispatch.get(msg['method'])
        if f:
            f( *msg['args'] )
        else:
            print("Invalid message %s" % str(msg)) 
    
    def __init__(self, s):
        self.s = s
        self.dispatch = {
            'noteon': self.noteon,
            'noteoff': self.noteoff,
            'prog': self.prog,
            'pitch_bend': self.pitch_bend,
            'pitch_bend_range': self.pitch_bend_range
        }


class FluidSynthClient(Thread):
    """
    This is a thin wrapper around the fluidsynth TCP interface
    that sends events to the server within an internal thread.
    """
    
    
    def __init__(self):
        super().__init__(daemon=True)
        self.s = socket(AF_INET, SOCK_STREAM)
        self.q = Queue()    
        self.dispatcher = fluid_synth_dispatcher(self.s)
        
    def __del__(self):
        self.c.close()    
        
    def connect(self, port, addr='127.0.0.1'):
        self.s.connect((addr, port))
    
    def service_one_event(self, t=None):
        msg = self.q.get(timeout=t)
        self.dispatcher.proc_msg(msg)
    
    def run(self):
        while True:
            self.service_one_event()                
    #
    # - client api and internal 
    #
    def noteon(self, chan, key, vel):
        msg = {
            'method': 'noteon',
            'args': (chan, key, vel)
        }
        self.q.put(msg)
    
    def noteoff(self, chan, key):
        msg = {
            'method': 'noteoff',
            'args': (chan, key)
        }
        self.q.put(msg)

    def prog(self, chan, instrument):
        msg = {
            'method': 'prog',
            'args': (chan, instrument)
        }
        self.q.put(msg)

    def pitch_bend_range(self, chan, semitones):
        msg = {
            'method': 'pitch_bend_range',
            'args': (chan, semitones)
        }
        self.q.put(msg)

    def pitch_bend(self, chan, offset):
        msg = {
            'method': 'pitch_bend',
            'args': (chan, offset)
        }
        self.q.put(msg)

    
    
    
    
def unittest():
    import sys, time
    
    port = 2112
    addr = sys.argv[1]
    
    fsc = FluidSynthClient()    
    fsc.connect(port, addr)
    fsc.start()
    
    time.sleep(1)
    
    fsc.noteon(0, 60, 100)
    time.sleep(3)
    fsc.noteoff(0, 60)
    
    time.sleep(1)
    
    
    
    
if __name__ == '__main__':
    unittest()    
    
