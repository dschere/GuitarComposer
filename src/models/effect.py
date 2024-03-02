import glob, os, pickle

from common.config import PRESET_DIR
from models.param import Parameter, BoolParam, IntParam, FloatParam


EffectsSchema = {
   "group-order": ["volume","compressor","echo","reverb","chorus","flanger","distortion","misc"],
   "ffmpeg": {
       "volume": "volume=%f",
       "compressor":"ladspa=file=dyson_compress_1403:dysonCompress", 
       "distortion": "ladspa=file=guitarix_distortion:guitarix-distortion",
       "reverb1": "ladspa=file=tap_reverb:tap_reverb",
       "reverb2": "ladspa=file=guitarix_freeverb:guitarix_freeverb",
       "echo": "ladspa=file=tap_echo:tap_stereo_echo",
       "chorusflanger": "ladspa=file=tap_chorusflanger:tap_chorusflanger",
       "multivoicechorus": "ladspa=file=multivoice_chorus_1201:multivoiceChorus",
       "flanger": "ladspa=file=dj_flanger_1438:djFlanger",
       "octave":"ladspa=file=divider_1186:divider",
       "doubler":"ladspa=file=tap_doubler:tap_doubler",
       "tremolo":"ladspa=file=tap_tremolo:tap_tremolo",
    },
    "groups": {
        "volume": ["volume"],
        "compressor": ["compressor"],
        "distortion": ["distortion"],
        "reverb": ["reverb1","reverb2"],
        "echo": ["echo"],
        "chorus": ["chorusflanger","multivoicechorus"],
        "flanger": ["flanger"],
        "misc": ["octave",'doubler',"tremolo"]
    },
   "effects": {
        "tremolo": [
            FloatParam(name="frequency",defval=1.0,minval=0,maxval=20.0, label="Frequency [Hz]"),
            FloatParam(name="depth",defval=50.0,minval=0,maxval=100.0,label="Depth [%]"),
            FloatParam(name="gain",defval=0.0,minval=-70.0,maxval=20.0,label="Gain [dB]")
        ] ,
        "octave": [
        ],
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
        "doubler": [
            FloatParam(name="time", defval=0.5, minval=0, maxval=1.0, label="Time Tracking"),
            FloatParam(name="pitch", defval=0.5, minval=0, maxval=1.0, label="Pitch Tracking"),
            IntParam  (name="drylevel", defval=0, minval=-90, maxval=20, label="Dry Level [dB]"),
            BoolParam (name="dryleftposition",defval=False, label="Dry Left Position"), 
            BoolParam (name="dryrightposition",defval=True, label="Dry Right Position"), 
            IntParam  (name="wetlevel", defval=0, minval=-90, maxval=20, label="Wet Level [dB]"),
            BoolParam (name="wetLeftposition",defval=False, label="Wet Left Position"), 
            BoolParam (name="wetRightposition",defval=True, label="Wet Right Position"),             
        ],
        "compressor": [        
            IntParam(name="Peak limit",defval=0,minval=-30,maxval=0,label="Peak limit (dB)"),
            FloatParam(name="release",defval=0.25,minval=0.0,maxval=1.0,label="Release time (s)"),
            FloatParam (name="fcompressionratio",defval=0.5,minval=0,maxval=1.0,label="Fast compression ratio"),
            FloatParam(name="compressionratio",defval=0.5,minval=0.0,maxval=1.0,label="Compression ratio")
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
            IntParam  (name="L_Delay",defval=100,minval=0,maxval=2000,label="L Delay [ms]"),
            IntParam  (name="L_Feedback",defval=0,minval=0,maxval=100,label="L Feedback [%]"),
            IntParam  (name="R_Haas_Delay",defval=100,minval=0,maxval=2000,label="R/Haas Delay [ms]"),
            IntParam  (name="R_Haas_Feedback",defval=0,minval=0,maxval=100,label="R/Haas Feedback [%]"),
            IntParam  (name="L_echo_level",defval=0,minval=-70,maxval=10,label="L Echo Level [dB]"),
            IntParam  (name="R_echo_level",defval=0,minval=-70,maxval=10,label="R Echo Level [dB]"),
            IntParam  (name="drylevel",defval=0,minval=-70,maxval=10,label="Dry Level [dB]"),
            BoolParam (name="crossmode",defval=True,label="Cross Mode"),
            BoolParam (name="haaseffect",defval=False,label="Haas Effect"),
            BoolParam (name="swapoutputs",defval=False,label="Swap Outputs")
        ],
        "chorusflanger":[        
            FloatParam(name="freq",defval=1.25,minval=0.0,maxval=5.0,label="Frequency [Hz]"),
            IntParam  (name="phaseshift",defval=90,minval=0,maxval=180,label="L/R Phase Shift [deg]"),
            IntParam  (name="depth",defval=75,minval=0,maxval=100,label="Depth [%]"),
            IntParam  (name="delay",defval=25,minval=0,maxval=100,label="Delay [ms]"),
            IntParam  (name="contour",defval=100,minval=20,maxval=20000,label="Contour [Hz]"),
            IntParam  (name="drylevel",defval=0,minval=-90,maxval=20,label="Dry Level [dB]"),
            IntParam  (name="wetlevel",defval=0,minval=-90,maxval=20,label="Wet Level [dB]")
        ],
        "multivoicechorus":[
            IntParam  (name="numvoices",defval=1,minval=1,maxval=8,label="Number of voices"),
            IntParam  (name="delay_ms",defval=10,minval=10,maxval=40,label="Delay base (ms)"),
            FloatParam(name="voice_separation",defval=0.5,minval=0,maxval=2.0,label="Voice separation (ms)"),
            FloatParam(name="detune",defval=1.0,minval=0,maxval=5.0,label="Detune (%)"),
            IntParam  (name="lfo-freq",defval=9,minval=2,maxval=90,label="LFO frequency (Hz)"),
            IntParam  (name="attenuation",defval=0,minval=-20,maxval=0,label="Output attenuation (dB)")
        ],
        "flanger": [
            FloatParam(name="period",defval=1.0,minval=0.1,maxval=32,required=True,label="LFO period (s)"),
            FloatParam(name="depth",defval=4.0,minval=1.0,maxval=5.0,label="LFO depth (ms)" ),
            IntParam  (name="feedback",defval=0,minval=-100,maxval=100,label="Feedback (%)")
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
        # schema change since the time preset was made.
        if effect_name not in self.settings:
            plist = EffectsSchema['effects'][effect_name]
            self.settings[effect_name] = Effect(effect_name, plist)

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
    
