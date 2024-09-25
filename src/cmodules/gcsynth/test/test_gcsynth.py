#!/usr/bin/env python

import unittest
import os
import time
import json

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

    def test0103_start_stop(self):
        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        time.sleep(2)
        gcsynth.stop()

    def test0201_filter_info(self):
        path = "/usr/lib/ladspa/guitarix_compressor.so"
        label = "guitarix_compressor"
        info = gcsynth.query_filter(path, label)
        print(json.dumps(info, sort_keys=True, indent=4))    
    

    def test0202_filter_test(self):
        path = "/usr/lib/ladspa/guitarix_compressor.so"
        label = "guitarix_compressor"
        test_status = gcsynth.test_filter(path, label)
        assert(test_status == True)

        #assert(test_status == True)    
    


if __name__ == '__main__':
    unittest.main()