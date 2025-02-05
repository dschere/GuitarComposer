from models.param import EffectParameter

# import from native C library. 
from gcsynth import filter_query as effect_param_specifcation # type: ignore
from collections import OrderedDict
import os 


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
        self.params = OrderedDict()
        self.enabled = False

        specList = effect_param_specifcation(self.path, self.plugin)
        for spec in specList:
            ep = EffectParameter(spec) 
            self.params[ep.name] = ep
        
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
        return self.plugin


class Distortion(EffectModule):
    def __init__(self):
        filename = "guitarix_distortion.so"
        self.label = "guitarix-distortion"
        super().__init__(filename, self.label) 

    def name(self):
        return "distortion"

class Reverb(EffectModule):
    def __init__(self):
        filename = "tap_reverb.so"
        self.label = "tap_reverb"
        super().__init__(filename, self.label) 

    def name(self):
        return "reverb"

class Echo(EffectModule):
    def __init__(self):
        filename = "tap_echo.so"
        self.label = "tap_stereo_echo"
        super().__init__(filename, self.label) 

    def name(self):
        return "echo"


class ChorusFlanger(EffectModule):
    def __init__(self):
        filename = "tap_chorusflanger.so"
        self.label = "tap_chorusflanger"
        super().__init__(filename, self.label) 

    def name(self):
        return "chorus-flanger"


class Effects:
    def __init__(self):
        self.distortion = Distortion()
        self.reverb = Reverb() 
        self.chorus_flanger = ChorusFlanger()
        self.echo = Echo()

    def enable_all(self):
        self.distortion.enable()
        self.reverb.enable() 
        self.chorus_flanger.enable() 
        self.echo.enable()



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
        
