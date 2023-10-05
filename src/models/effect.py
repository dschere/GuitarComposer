import glob, os, pickle

from common.config import PRESET_DIR
from models.param import Parameter, BoolParam, IntParam, FloatParam


EffectsSchema = {
   "group-order": ["volume","compressor","echo","reverb","chorus","flanger","distortion"],
   "ffmpeg": {
       "volume": "volume=%f",
       "compressor":"ladspa=file=dyson_compress_1403:dysonCompress", 
       "distortion": "ladspa=file=guitarix_distortion:guitarix-distortion",
       "reverb1": "ladspa=file=tap_reverb:tap_reverb",
       "reverb2": "ladspa=file=guitarix_freeverb:guitarix_freeverb",
       "echo": "ladspa=file=tap_echo:tap_stereo_echo",
       "chorusflanger": "ladspa=file=tap_chorusflanger:tap_chorusflanger",
       "multivoicechorus": "ladspa=file=multivoice_chorus_1201:multivoiceChorus",
       "flanger": "ladspa=file=dj_flanger_1438:djFlanger"
    },
    "groups": {
        "volume": ["volume"],
        "compressor": ["compressor"],
        "distortion": ["distortion"],
        "reverb": ["reverb1","reverb2"],
        "echo": ["echo"],
        "chorus": ["chorusflanger","multivoicechorus"],
        "flanger": ["flanger"]
    },
   "effects": {
        "volume": [
            FloatParam(name="gain",defval=1.0,minval=0,maxval=20.0)
        ],   
        "distortion": [
            FloatParam(name="overdrive",defval=10.5,minval=1,maxval=20),
            BoolParam (name="driveove",defval=False),
            FloatParam(name="drive",defval=0.5,minval=0,maxval=1.0),
            FloatParam(name="drivelevel",defval=0.0,minval=0,maxval=1.0),
            FloatParam(name="drivegain",defval=0.0,minval=-20.0,maxval=20.0),            
            IntParam  (name="highpass",defval=256,minval=8,maxval=1000),
            IntParam  (name="lowpass",defval=5500,minval=1000,maxval=10000),
            BoolParam (name="lowhighpass",defval=True),
            IntParam  (name="highcut",defval=5500,minval=1000,maxval=10000),
            IntParam  (name="lowcut",defval=256,minval=8,maxval=1000),
            BoolParam (name="lowhighcut",defval=True),
            FloatParam(name="trigger",defval=1.0,minval=0,maxval=1.0),
            FloatParam(name="vibrato",defval=1.0,minval=0.01,maxval=1.0)
        ],
        "compressor": [
            IntParam(name="Peak limit",defval=0,minval=-30,maxval=0),
            FloatParam(name="release",defval=0.25,minval=0.0,maxval=1.0),
            FloatParam (name="fcompressionratio",defval=0.5,minval=0,maxval=1.0),
            FloatParam(name="compressionratio",defval=0.5,minval=0.0,maxval=1.0)
        ],
        "reverb1": [
            IntParam  (name="decay",defval=2500,minval=0,maxval=10000),
            IntParam  (name="drylevel",defval=0,minval=-70,maxval=10),
            IntParam  (name="wetlevel",defval=0,minval=-70,maxval=10),
            BoolParam (name="combfilters",defval=True),
            BoolParam (name="allpassfilters",defval=True),
            BoolParam (name="bandfilters",defval=True),
            BoolParam (name="balancedfilters",defval=True),
            IntParam  (name="reverbtype",defval=0,minval=0,maxval=42)
        ],
        "reverb2": [
            FloatParam(name="roomsize",defval=0.5,minval=0,maxval=1.0),
            FloatParam(name="damp",defval=0.5,minval=0,maxval=1.0),
            FloatParam(name="drywet",defval=0.25,minval=0,maxval=1.0)
        ],
        "echo": [
            IntParam  (name="L_Delay",defval=100,minval=0,maxval=2000),
            IntParam  (name="L_Feedback",defval=0,minval=0,maxval=100),
            IntParam  (name="R_Haas_Delay",defval=100,minval=0,maxval=2000),
            IntParam  (name="R_Haas_Feedback",defval=0,minval=0,maxval=100),
            IntParam  (name="L_echo_level",defval=0,minval=-70,maxval=10),
            IntParam  (name="R_echo_level",defval=0,minval=-70,maxval=10),
            IntParam  (name="drylevel",defval=0,minval=-70,maxval=10),
            BoolParam (name="crossmode",defval=True),
            BoolParam (name="haaseffect",defval=False),
            BoolParam (name="swapoutputs",defval=False)
        ],
        "chorusflanger":[
            FloatParam(name="freq",defval=1.25,minval=0.0,maxval=5.0),
            IntParam  (name="phaseshift",defval=90,minval=0,maxval=180),
            IntParam  (name="depth",defval=75,minval=0,maxval=100),
            IntParam  (name="delay",defval=25,minval=0,maxval=100),
            IntParam  (name="contour",defval=100,minval=20,maxval=20000),
            IntParam  (name="drylevel",defval=0,minval=-90,maxval=20),
            IntParam  (name="wetlevel",defval=0,minval=-90,maxval=20)
        ],
        "multivoicechorus":[
            IntParam  (name="numvoices",defval=1,minval=1,maxval=8),
            IntParam  (name="delay_ms",defval=10,minval=10,maxval=40),
            FloatParam(name="voice_separation",defval=0.5,minval=0,maxval=2.0),
            FloatParam(name="detune",defval=1.0,minval=0,maxval=5.0),
            IntParam  (name="lfo-freq",defval=9,minval=2,maxval=90),
            IntParam  (name="attenuation",defval=0,minval=-20,maxval=0)
        ],
        "flanger": [
            FloatParam(name="period",defval=1.0,minval=0.1,maxval=32,required=True),
            FloatParam(name="depth",defval=4.0,minval=1.0,maxval=5.0),
            IntParam  (name="feedback",defval=0,minval=-100,maxval=100)
        ]
    }
}


# represents the seetings for a specific audio effect
class Effect:
    def __init__(self, name, plist):
        self.name = name
        self.enabled_p = BoolParam(
            name="enable",
            defval=False)
        self.plist = plist
        
    def setEnabled(self, value):
        self.enabled_p.value = value
        
    def isEnabled(self):
        return self.enabled_p.value
        
    def getPlist(self):
        return self.plist    
            
class EffectPresets:
    def __init__(self, preset_name):
        self.preset_name = preset_name
        self.settings = {}
         
        for (effect_name,plist) in EffectsSchema['effects'].items():
            self.settings[effect_name] = Effect(effect_name, plist)
                
    def getEnabledParam(self, effect_name):
        return self.settings[effect_name].enabled_p        
        
    def getParamList(self, effect_name):
        return self.settings[effect_name].plist

    def getStoredPresets(self):
        names = []

        for file_path in glob.glob(PRESET_DIR+"*"):
            base_name = os.path.basename(file_path)
            preset_name, _ = os.path.splitext(base_name)
            names.append( preset_name)
            
        return names    
        
    def save(self, preset_name=None):
        if not preset_name:
            preset_name = self.preset_name
        data = pickle.dumps(self.settings)
        f = open( PRESET_DIR+preset_name, "wb" )
        f.write( data )
        
    def preset_exists(self, preset_name):
        return os.access(PRESET_DIR+preset_name,os.F_OK)
        
    def load(self, preset_name):
        if os.access(PRESET_DIR+preset_name,os.F_OK):
            data = open( PRESET_DIR+preset_name, "rb" ).read()
            self.settings = pickle.loads(data)
            self.preset_name = preset_name
    
    def remove(self, preset_name):
        path = PRESET_DIR+preset_name
        if os.access(path,os.F_OK):
            os.remove(path)
          
def unittest():
    p = EffectPresets("test-test")
    
    p.save()
    
    p.settings['volume'].setEnabled(True)    
    p.load("test-test")
    assert( p.settings['volume'].isEnabled() == False)
    p.remove()
    
if __name__ == '__main__':
    unittest()    
    
