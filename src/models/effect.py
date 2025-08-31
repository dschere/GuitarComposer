from typing import Dict, List, Tuple
from models.param import EffectParameter

# import from native C library. 
from gcsynth import filter_query as effect_param_specifcation # type: ignore
from collections import OrderedDict
import os 
import json
import copy


"""
Each TabEvent can have a Effects() object or None
The Effects contains all effects the user selected by clicking on
the effects icon.

When the track is played a local Effects() object is created by the 
player. This will be used are a reference to switch on/off effects
or to change prarameters.

The Effects object by default contains an empty etable
the existance of entry implies that the effect is turned on.
"""



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
    def __init__(self, delta_r = {}):
        # label -> Effect instance
        self.etable = {}
        self.etable.update(delta_r)

    # EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]
    def get_changes(self, other):
        curr_enabled = set(self.etable.keys())
        diff = {}

        if other is not None:
            other_enabled = set(other.etable.keys())
            # get effects to be disabled
            for label in (other_enabled - curr_enabled):
                e : Effect = copy.deepcopy(other.etable[label])
                e.disable()
                diff[e] = []
        # get the effects to be aletered or enabled
        for e in self.get_enabled_effects():
            e : Effect = copy.deepcopy(e)
            e.enable()
            diff[e] = e.params.items()
        return diff

    def add(self, label: str, e: Effect):
        self.etable[label] = e

    def get_enabled_effects(self) -> List[Effect]:
        return list(self.etable.values())   

    def get_effect(self, label: str) -> Effect | None:
        from services.effectRepo import EffectRepository
        if label in self.etable:
            return self.etable[label]
        else:
            ef = EffectRepository()
            return copy.deepcopy(ef.get(label))

    def get_names(self) -> List[str]:
        from services.effectRepo import EffectRepository
        ef = EffectRepository()
        r = ef.getNames()
        r.sort()
        return r

    def delta(self, original): 
        """ 
        Return a dictionary of enabled effects and the parameters the user 
        selected.
        """
        r = {}
    
        for n in self.get_names():
            e = self.get_effect(n)
            
            if original is not None:
                orig_e = original.get_effect(n)
            else:
                orig_e = None

            assert(e)
            if not orig_e and e.is_enabled():
                e = copy.deepcopy(e)
                r[e.label] = e
                 
            # effect was enabled but now its disabled
            elif not e.is_enabled():
                pass

            # effect was disabled but now its enabled.
            elif orig_e and not orig_e.is_enabled() and e.is_enabled():
                e = copy.deepcopy(e)
                r[e.label] = e
                                
            # effect remained enabled, see if there are any
            # parameter changes, if so make an entry
            elif orig_e and orig_e.is_enabled() and e.is_enabled():
                diff = []
                for n in e.getParamNames():
                    ep = e.get_param_by_name(n)
                    o_ep = orig_e.get_param_by_name(n)
                    if ep.current_value != o_ep.current_value:
                        diff.append((n,ep))
                if len(diff) > 0:
                    e = copy.deepcopy(e)
                    r[e.label] = e
                
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
        
