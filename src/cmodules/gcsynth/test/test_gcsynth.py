#!/usr/bin/env python

import unittest
import os
import time
import json
import sys

import gcsynth


base_dir = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-5])


class TestGcSynth(unittest.TestCase):

    
    def test0101_start(self):
        fake_data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
            "test": True
        }
        gcsynth.start(fake_data)

    def test0102_start_error(self):
        fake_data = {
            "test": True
        }
        success = False
        try:
            gcsynth.start(fake_data)
            
        except gcsynth.GcsynthException:
            print("success, forced an exception and was caght!")   
            success = True
        assert(success)
        
    def test0103_start_play_stop(self):
        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        time.sleep(1.0)
        gcsynth.noteon(0, 70, 40)
        time.sleep(0.5)
        gcsynth.noteoff(0, 70)

        gcsynth.stop()

    
    def test0201_filter_info(self):
        path = "/usr/lib/ladspa/guitarix_compressor.so"
        label = "guitarix_compressor"
        info = gcsynth.query_filter(path, label)
        print(json.dumps(info, sort_keys=True, indent=4))    
         

    
    def test0202_filter_test(self):
        path = "/usr/lib/ladspa/guitarix_distortion.so"
        label = "guitarix-distortion"
        gcsynth.test_filter(path, label)
        
    def test0301_apply_filter_test(self):
        path = "/usr/lib/ladspa/guitarix_echo.so"
        label = "guitarix_echo"

        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        gcsynth.add_filter(0,path,label)
        gcsynth.noteon(0, 70, 40)
        time.sleep(4.0)
        gcsynth.noteoff(0, 70)
        gcsynth.stop()
        gcsynth.remove_filter(0,label)


    def test0302_apply_filter_test(self):
        path = "/usr/lib/ladspa/guitarix_echo.so"
        label = "guitarix_echo"

        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        gcsynth.noteon(0, 70, 40)
        time.sleep(0.25)
        print("apply filter during play")
        gcsynth.add_filter(0,path,label)
        time.sleep(3.75)
        gcsynth.noteoff(0, 70)
        gcsynth.stop()



if __name__ == '__main__':
    unittest.main()
    print("after unit tests")