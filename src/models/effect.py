from models.param import (ParameterFactory,
                          EffectParamBase, 
                          BooleanEffectParam, 
                          IntegerEffectParam, 
                          FloatingEffectParam)

# import from native C library. 
from gcsynth import filter_query as effect_param_specifcation # type: ignore
from collections import OrderedDict
import os 



class PresentationBase:
    def __init__(self, p : EffectParamBase):
        self.p = p

    def getValue(self):
        return self.p.getValue() 
    
    def setValue(self, v):
        self.p.setValue(v)

class CheckboxPresentation(PresentationBase):
    def __init__(self, p : BooleanEffectParam ):
        super().__init__(p)


class SliderPresentation(PresentationBase):
    def __init__(self, p : EffectParamBase ):
        super().__init__(p)

    def choices(self):
        "return an array of value choices that the user will be able to select from"
        if isinstance(self.p, IntegerEffectParam):
            low = int(self.p.lower_bound()) 
            high = int(self.p.upper_bound())
            return range(low, high+1)
        else:
            r = []
            low = self.p.lower_bound() 
            high = self.p.upper_bound()
            prev = None 
            dv = self.p.get_default_value() 
            assert(dv)
            for i in range(0,100):
                d = (high-low)
                v = ((d * i)/100) + low
                if prev:
                    if prev < dv <= v:
                        # subsitute with default value.
                        v = dv
                r.append(v)        
                prev = v
            assert(dv in r)    
            return r

class EffectModule:
    """
    This object represents the paramters of a given ladspa effect.

    Being a persitent object it needs to be initialized before use.
    This is bootstrap operation that needs to be used only once.
    """

    def __init__(self, ladspa_libname : str, ladspa_plugin : str):
        path = os.environ.get('LADSPA_PATH','/usr/lib/ladspa')
        ladspa_path = path + "/" + ladspa_libname
        # path to ladspa shared library
        self.path = ladspa_path 
        # plugin within library (there can be multiple)
        self.plugin = ladspa_plugin
        self.initialized = False
        self.params = OrderedDict()
        self.enabled = False
        
    def enable(self):
        self.bootstrap()
        self.enabled = True 

    def disable(self):
        self.enabled = False        

    def load_factory_defaults(self):
        specList = effect_param_specifcation(self.path, self.plugin)
        for spec in specList:
            ep = ParameterFactory(spec)
            if isinstance(ep, BooleanEffectParam):
                pres = CheckboxPresentation(ep)
                self.params[ep.name()] = pres
            elif ep.has_lower_bound() and ep.has_upper_bound():
                # bounded values are represented as sliders
                pres = SliderPresentation(ep)
                self.params[ep.name()] = pres
                    

    def bootstrap(self):
        "if not initialized then load parameters using the gcsynth method"
        if not self.initialized:
            self.load_factory_defaults()
            self.initialized = True


class Distortion(EffectModule):
    def __init__(self):
        filename = "guitarix_distortion.so"
        self.label = "guitarix-distortion"
        super().__init__(filename, self.label) 

class Reverb(EffectModule):
    def __init__(self):
        filename = "tap_reverb.so"
        self.label = "tap_reverb"
        super().__init__(filename, self.label) 

class ChorusFlanger(EffectModule):
    def __init__(self):
        filename = "tap_chorusflanger.so"
        self.label = "tap_chorusflanger"
        super().__init__(filename, self.label) 



class Effects:
    def __init__(self):
        self.distortion = Distortion()
        self.reverb = Reverb() 
        self.chorus_flanger = ChorusFlanger()
        
