""" 
Launches a fluidsynth process using the TCP interface.
"""

import subprocess
import shlex
import os
import socket
import time
import atexit
import singleton_decorator

from guitarcomposer.util.find_free_tcp_port import find_free_tcp_port

import guitarcomposer.common.resources as R

DEFAULT_CONNECT_TCP_TIMEOUT = float(os.environ.get("GUITARCOMOPOSER_TCP_TIMOUT","5"))


class fs_api_interface:
    def noteon(self, fret, string, vel):
        pass

    def noteoff(self, fret, string):
        pass

    def pitch_bend_range(self, string, semitones):
        pass

    def pitch_bend(self, string, vel):
        pass

    def clear_pitch_bend(self, string):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    

class api:
    def __init__(self, **config):
        self.proc = None
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.config = config

    def start(self):
        sf_filename = R.DEFAULT_SOUND_FONT
        if self.config.get("guitar",False):
            sf_filename = R.GUITAR_SOUND_FONT

        # search for a free TCP port number to use.
        self.port = find_free_tcp_port()
        cmd = "%s %d %s" % (R.FLUID_SYNTH_SCRIPT,self.port,sf_filename)
        self.proc = subprocess.Popen(shlex.split(cmd))

        conn_expire = time.time() + DEFAULT_CONNECT_TCP_TIMEOUT
        while True:
            try:
                self.s.connect( ('',self.port) )
                break # <-- break out of while loop
            except ConnectionRefusedError:
                if time.time() > conn_expire:
                    raise TimeoutError("Unable to connect to fluidsynth instance")
                time.sleep(0.25)

        # cleanup incase we crash
        atexit.register(self.stop)

    def stop(self):
        if self.proc and not self.proc.poll():
            self.proc.terminate()
            self.proc.communicate()
            self.proc.wait()

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

    def pitch_bend(self, chan, val):
        offset = int(8192.0 + (4096.0 * val))

        msg = f"pitch_bend {chan} {offset}\n"
        self.s.sendall(msg.encode('utf-8'))        

            

def unittest_guitar_api():
    from guitarcomposer.model.track import standard_tuning
    from guitarcomposer.services.fluidsynth.fs_guitar_api import fs_guitar_api
    
    g_fs_api = fs_guitar_api(standard_tuning)
    g_fs_api.start()

    g_fs_api.noteon(7,1,127)
    for i in range(0,10):
        g_fs_api.pitch_bend(1,i * 0.1)
        time.sleep(0.1)
    time.sleep(2)
    

    g_fs_api.stop()


def unittest_api():
    fs_api = api(guitar=True)
    fs_api.start()
    fs_api.prog(0, 0)
    fs_api.prog(1, 1)
    fs_api.prog(2, 2)
    fs_api.prog(3, 3)
    fs_api.prog(4, 4)
    fs_api.prog(5, 5)
    # 120 bpm quater note is 0.5 secs 
    step = 0.5 / 6 # take 1 beat to complete downstrum
    e_major = [40,47,52,56,59,64]

    for (gstring,midi) in enumerate(e_major):
        fs_api.noteon(gstring, midi, 100)
        time.sleep(step)

    time.sleep(3.5)

    fs_api.stop()

if __name__ == '__main__':
    print("api test")
    #unittest_api()            
    unittest_guitar_api()