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
        data = {"sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
        gcsynth.start(data)
        #gcsynth.noteon(0, 60, 100)
        noteon(2000, 0, 60, 100).send()
        print("sleeping for 3 seconds should play in background")
        time.sleep(3.0)
        gcsynth.stop()    
        print("end test1")

    def test02_note_inflight_ignore_on_restart(self):
        data = {"sfpaths": [
            "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
        gcsynth.start(copy.deepcopy(data))
        noteon(2000, 0, 65, 100).send()
        time.sleep(0.1)
        gcsynth.stop()

        gcsynth.start(copy.deepcopy(data))
        print("should have heard no sound!")
        time.sleep(3.0)
        gcsynth.stop()

    def test03_strum_a_chord(self):
        data = {"sfpaths": [
            "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
        gcsynth.start(copy.deepcopy(data))

        chord = [
            vars(noteon(1000, 0, 65, 100)),
            vars(noteon(1020, 1, 60, 100)),
            vars(noteon(1040, 2, 55, 100)),
            vars(noteon(1040, 3, 50, 100))
        ]
        gcsynth.timer_event(chord)
        print("should hear an upstroke")
        time.sleep(3.0)
        gcsynth.stop()
        print("end test3")

    def test04_strum_a_chord(self):
        data = {"sfpaths": [
            "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
        gcsynth.start(copy.deepcopy(data))

        chord = [
            vars(noteon(1000, 0, 65, 100)),
            vars(noteon(1020, 1, 60, 100)),
            vars(noteon(1040, 2, 55, 100)),
            vars(noteon(1040, 3, 50, 100))
        ]
        gcsynth.timer_event(chord)
        gcsynth.reset_channel(0)
        gcsynth.reset_channel(1)
        gcsynth.reset_channel(2)
        gcsynth.reset_channel(3)

        print("should hear nothing since channels are reset prior to play!")
        time.sleep(3.0)
        gcsynth.stop()
        print("end test 4")
        time.sleep(3)


    def test00_print_filter_info(self):
        data = {"sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
        gcsynth.start(data)

        ladspa_path = "/usr/lib/ladspa/guitarix_distortion.so"
        ladspa_label = "guitarix-distortion"

        spec = gcsynth.filter_query(ladspa_path, ladspa_label)
        for pinfo in spec:
            print(pinfo) 

        time.sleep(1.0)
        gcsynth.stop()
        print("existing test 0")    

if __name__ == '__main__':
    unittest.main()
    print("after unit tests")
