from typing import List
from models.param import EffectParameter

# import from native C library. 
from gcsynth import filter_query as effect_param_specifcation # type: ignore
from collections import OrderedDict
import os 
import json
import copy

class ControlMeta:
    def __init__(self, data : dict):
        for (k,v) in data.items():
            setattr(self, k, v)
            
class Effect:
    "represents an audio effect"

    version = "1.0"

    def __init__(self, name, label, path, controls):
        self.name = name 
        self.label = label
        # has this effect been selected for use ?
        self.selected = False
        self.path = path
        self.enabled = False
        self.params = OrderedDict() # type: ignore
        self.controls = controls

        for c in controls:
            ep = EffectParameter(c)
            self.params[ep.name] = ep    

    def json_data(self):
        "return data that can be ecoded in json."
        d = copy.deepcopy(vars(self))
        del d['params']
        return d
    
    def getParamNames(self) -> List[str]:
        return list(self.params.keys())
    
    def getParameters(self) -> list[EffectParameter]:
        return list(self.params.values())

    def select(self):
        "If this plugin available for use."
        self.selected = True

    def unselect(self):
        self.selected = False            

    def enable(self):
        self.enabled = True 

    def disable(self):
        self.enabled = False        

    def is_enabled(self):
        return self.enabled    

    def name(self):
        return ""        
    
    def plugin_path(self):
        return self.path 
    
    def plugin_label(self):
        return self.label

    def get_name(self) -> str:
        return self.name 

    def get_param_by_name(self, name) -> EffectParameter:
        return self.params[name] 
        
    
    

# class EffectModule:
#     """
#     This object represents the paramters of a given ladspa effect.

#     Being a persitent object it needs to be initialized before use.
#     This is bootstrap operation that needs to be used only once.
#     """

#     def __init__(self, ladspa_libname : str, ladspa_plugin : str):
#         path = os.environ.get('LADSPA_PATH','/usr/lib/ladspa')
#         ladspa_path = path + "/" + ladspa_libname
#         # path to ladspa shared library
#         self.path = ladspa_path 
#         # plugin within library (there can be multiple)
#         self.plugin = ladspa_plugin
#         self.params = OrderedDict()
#         self.enabled = False

#         specList = effect_param_specifcation(self.path, self.plugin)
#         for spec in specList:
#             ep = EffectParameter(spec) 
#             self.params[ep.name] = ep
        
#     def enable(self):
#         self.enabled = True 

#     def disable(self):
#         self.enabled = False        

#     def is_enabled(self):
#         return self.enabled    

#     def name(self):
#         return ""        
    
#     def plugin_path(self):
#         return self.path 
    
#     def plugin_label(self):
#         return self.plugin



# class Distortion(EffectModule):
#     def __init__(self):
#         filename = "guitarix_distortion.so"
#         self.label = "guitarix-distortion"
#         super().__init__(filename, self.label) 

#     def name(self):
#         return "distortion"

# class Reverb(EffectModule):
#     def __init__(self):
#         filename = "tap_reverb.so"
#         self.label = "tap_reverb"
#         super().__init__(filename, self.label) 

#     def name(self):
#         return "reverb"

# class Echo(EffectModule):
#     def __init__(self):
#         filename = "tap_echo.so"
#         self.label = "tap_stereo_echo"
#         super().__init__(filename, self.label) 

#     def name(self):
#         return "echo"


# class ChorusFlanger(EffectModule):
#     def __init__(self):
#         filename = "tap_chorusflanger.so"
#         self.label = "tap_chorusflanger"
#         super().__init__(filename, self.label) 

#     def name(self):
#         return "chorus-flanger"


class Effects:
    def __init__(self):
        # label -> Effect instance
        self.etable = {}

    def add(self, label: str, e: Effect):
        self.etable[label] = e

    def get_effect(self, label: str) -> Effect | None:
        return self.etable.get(label)

    def get_names(self) -> List[str]:
        r = list(self.etable.keys())
        r.sort()
        return r



def unittest():
    import gcsynth
    import copy 

    data = {"sfpaths": [
        "/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
    gcsynth.start(copy.deepcopy(data))
    
    e = Effects() 

    e.distortion.enable() 
    e.reverb.enable() 
    e.chorus_flanger.enable() 

    print(e.distortion.params)
    print(e.reverb.params)
    print(e.chorus_flanger.params)


    gcsynth.stop()


if __name__ == '__main__':
    unittest()        
        
