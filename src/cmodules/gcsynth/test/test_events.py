""" 
Test the capability of setting up events which will
be the basis of 'hand' effcts like bends/slides etc.

* test fluid synth events
* test effect events
"""

import unittest
import os
import time
import json
import sys
import copy

import gcsynth

from unit_test_util import *


class Test_GcSynth_Events(unittest.TestCase):
    
    def test01_note_on(self):
        data = { "sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"] }
        gcsynth.start(data) 
        noteon(2000,0,60,100).send()
        print("sleeping for 3 seconds should play in background")
        time.sleep(3.0)
        gcsynth.stop()

    def test02_note_inflight_ignore_on_restart(self):
        data = { "sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"] }
        gcsynth.start(copy.deepcopy(data)) 
        noteon(2000,0,65,100).send()
        time.sleep(0.1)
        gcsynth.stop()
        
        gcsynth.start(copy.deepcopy(data)) 
        print("should have heard no sound!")
        time.sleep(3.0)
        gcsynth.stop()

    def test03_strum_a_chord(self):
        data = { "sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"] }
        gcsynth.start(copy.deepcopy(data)) 

        chord = [
            vars(noteon(1000,0,65,100)),
            vars(noteon(1020,1,60,100)),
            vars(noteon(1040,2,55,100)),
            vars(noteon(1040,3,50,100))
        ]
        gcsynth.timer_event(chord)
        print("should hear an upstroke")
        time.sleep(3.0)
        gcsynth.stop()




if __name__ == '__main__':
    unittest.main()
    print("after unit tests")