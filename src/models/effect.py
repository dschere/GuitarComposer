from typing import Dict, List, Tuple
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


    # Note: I wanted to declare the type EffectChange
    def delta(self, original): 
        """ 
        Return a set of parameters for each effect that has been changed by the user.

        original is a copy of the effects that existed previously, return
        what has changed.

        EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]
        """
        r = {}
    
        for n in self.get_names():
            e = self.get_effect(n)
            orig_e = original.get_effect(n)
            assert(e)
            if not orig_e:
                # rare case where we have actually added a new effect?
                # in any case treat as if we are transitioning from
                # disabled to enabled.
                r[e] = [(n, e.get_param_by_name(n)) for n in e.getParamNames()]
                 
            # effect was enabled but now its disabled
            elif orig_e.is_enabled() and not e.is_enabled():
                if orig_e and orig_e.is_enabled():
                    r[e] = []

            # effect was disabled but now its enabled.
            elif not orig_e.is_enabled() and e.is_enabled():
                r[e] = [(n, e.get_param_by_name(n)) for n in e.getParamNames()]
                                
            # effect remained enabled, see if there are any
            # parameter changes, if so make an entry
            elif orig_e.is_enabled() and e.is_enabled():
                diff = []
                for n in e.getParamNames():
                    ep = e.get_param_by_name(n)
                    o_ep = orig_e.get_param_by_name(n)
                    if ep.current_value != o_ep.current_value:
                        diff.append((n,ep))
                if len(diff) > 0:
                    r[e] = diff 

            else:
                # both was and is disabled, skip
                pass
        
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
        
