"""
Given a model.EffectPresets instance configure ffmpeg to play and
possibly record an audio file. This service maintains an instance
of an ffmpeg process. 
"""
import subprocess
import shlex
import logging


"""
effects_settings schema from js
 
effects_settings[<effect name>] = {
    "enabled": True|false,
    "plist": [{
        name,
        value,
        defval
    }, ...]
}

The collating order of the 'plist' matched the
order in the ladspa plugin. This is important since
ffmpeg uses this order as the index of an array rather
then the name of a parameter.

>> analyseplugin /usr/lib/ladspa/tap_reverb.so 

Plugin Name: "TAP Reverberator"
Plugin Label: "tap_reverb"
Plugin Unique ID: 2142
Maker: "Tom Szilagyi"
Copyright: "GPL"
Must Run Real-Time: No
Has activate() Function: Yes
Has deactivate() Function: No
Has run_adding() Function: Yes
Environment: Normal
Ports:  "Decay [ms]" input, control, 0 to 10000, default 2500    
        "Dry Level [dB]" input, control, -70 to 10, default 0
        "Wet Level [dB]" input, control, -70 to 10, default 0
        "Comb Filters" input, control, toggled, default 1
        "Allpass Filters" input, control, toggled, default 1
        "Bandpass Filter" input, control, toggled, default 1
        "Enhanced Stereo" input, control, toggled, default 1
        "Reverb Type" input, control, 0 to 42, default 0, integer

so in ffmpeg 
   -af "ladspa=file=tap_reverb:tap_reverb:controls=c0=5000"

c0 -> Decay
c1 -> Dry Level
c2 -> wet level
...

"""

from models.effect import EffectsSchema
from common.config import LIVEAUDIO_DIR

class LiveAudioPlayer:
    play_template = """ffplay -nodisp  -analyzeduration 1 
       -fflags nobuffer 
       -f alsa %(capture)s 
       -af "%(af)s" -ac 2 """
    
    record_template = """ffmpeg -analyzeduration 1 
       -fflags nobuffer -y -re -v error
       -f alsa -i %(capture)s -ac 2  
        -filter_complex "asplit[wet_in][dry_in];[wet_in]%(af)s,asplit[wet][wet2];[dry_in]volume=1[dry]"
          -map "[wet]" 
            -f alsa default  
          -map "[wet2]"
           -f %(suffix)s "%(liveaudio_dir)s/%(filename)s"
          -map "[dry]"
            -f %(suffix)s "%(liveaudio_dir)s/dry-%(filename)s"  
       """
    
    
    def _ffmpeg_effect(self, name, effect, model):
        # either ladspa filter or volume
        af_cmd = EffectsSchema['ffmpeg'][name]
        plist = effect.getPlist()
        if name == 'volume':
            # special case just get the value for gain
            return af_cmd % plist[0].value
            
        controls = []
        for (i,param) in enumerate(plist):
            if param.isRequired() or param.changed():
                n = "c%d=%s" % (i,param.asFFmpegParam())
                controls.append(n)
         
        if len(controls) > 0:
            af_cmd += ":c=" + "|".join(controls)
        return af_cmd    

    
    def _create_audio_filter(self, model):
        """
        Create an ffmpeg audio fields using ladspa effects 
        """
        af_list = []
        for (name,effect) in model.settings.items():
            if effect.isEnabled():
                af_cmd = self._ffmpeg_effect(name, effect, model)
                af_list.append(af_cmd) 
        return ",".join(af_list)    
    
    
    def __init__(self, capture, model, filename):
        af = self._create_audio_filter( model )
        liveaudio_dir = LIVEAUDIO_DIR
        if len(filename) == 0:
            cmd = self.play_template % locals()
        else:
            suffix = filename.split('.')[-1]
            cmd = self.record_template % locals()
        logging.info("Executing:\n%s" % ' '.join(shlex.split(cmd)))
        self.args = shlex.split(cmd)
        
    def start(self):
        logging.info(str(self.args))    
        self.proc = subprocess.Popen(self.args) 
        
    def stop(self):
        self.proc.terminate()
        try:
            self.proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.communicate()
        logging.info("shut down capture")    
         


