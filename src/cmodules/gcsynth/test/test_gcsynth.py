#!/usr/bin/env python

import unittest
import os
import time
import json
import sys

import gcsynth


base_dir = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-5])


class TestGcSynth(unittest.TestCase):

    """
    def test0101_start(self):
        print("test0101_start")
        fake_data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
            "test": True
        }
        gcsynth.start(fake_data)

    def test0102_start_error(self):
        print("test0102_start_error")
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
        print("test0103_start_play_stop")
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
        print("test0201_filter_info")
        path = "/usr/lib/ladspa/guitarix_compressor.so"
        label = "guitarix_compressor"
        info = gcsynth.filter_query(path, label)
        print(json.dumps(info, sort_keys=True, indent=4))    



    def test0202_filter_test(self):
        print("test0202_filter_test")
        path = "/usr/lib/ladspa/guitarix_distortion.so"
        label = "guitarix-distortion"
        gcsynth.test_filter(path, label)
    """

    def test0301_apply_filter_test(self):
        print("test0301_apply_filter_test")
        path = "/usr/lib/ladspa/tap_reverb.so"
        label = "tap_reverb"

        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        info = gcsynth.filter_query(path, label)
        print(json.dumps(info, sort_keys=True, indent=4))

#        print("1"); time.sleep(0.01)
        gcsynth.start(data)

        # print(json.dumps(sf_info, sort_keys=True, indent=4))

        gcsynth.select(0, 1, 1, 95)

        gcsynth.noteon(0, 60, 60)
        gcsynth.noteon(0, 65, 60)

        time.sleep(5.0)

        gcsynth.filter_add(0, path, label)
        gcsynth.filter_enable(0, label)
        # gcsynth.filter_set_control_by_index(0,label,0,440.0)
        # gcsynth.filter_set_control_by_index(0,label,1,1)

        """
            {"filter_set_control_by_index", py_gcsynth_channel_set_control_by_index, 
        METH_VARARGS,"filter_set_control_by_name(chan,plugin_label,index,value)" },

        """

        gcsynth.noteon(0, 60, 60)
        gcsynth.noteon(0, 65, 60)

#        print("2"); time.sleep(0.01)

        time.sleep(10.0)

        gcsynth.stop()
#        print("3"); time.sleep(0.01)

        gcsynth.filter_remove(0, label)
#        print("4"); time.sleep(0.01)

    """
    def test0302_apply_filter_test(self):
        print("test0302_apply_filter_test")
        path = "/usr/lib/ladspa/guitarix_echo.so"
        label = "guitarix_echo"

        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        gcsynth.noteon(0, 70, 40)
        time.sleep(0.25)
        print("apply filter during play")
        gcsynth.filter_add(0,path,label)
        time.sleep(3.75)
        gcsynth.noteoff(0, 70)
        gcsynth.stop()
    """


if __name__ == '__main__':
    unittest.main()
    print("after unit tests")
