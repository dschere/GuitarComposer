import unittest

from services.liveaudio import LiveAudioPlayer


EXPECTED_FFMPEG = "ffplay -nodisp -analyzeduration 1 -fflags nobuffer -f alsa hw:0 -af volume=8.000000,ladspa=file=guitarix_compressor:guitarix_compressor:c=c0=10|c1=10|c2=-30|c5=36.48,ladspa=file=tap_echo:tap_stereo_echo:c=c0=560|c1=44|c2=560|c3=43,ladspa=file=tap_reverb:tap_reverb:c=c0=8000,ladspa=file=tap_chorusflanger:tap_chorusflanger -ac 2"
EXPECTED_AF = "volume=8.000000,ladspa=file=guitarix_compressor:guitarix_compressor:c=c0=10|c1=10|c2=-30|c5=36.48,ladspa=file=tap_echo:tap_stereo_echo:c=c0=560|c1=44|c2=560|c3=43,ladspa=file=tap_reverb:tap_reverb:c=c0=8000,ladspa=file=tap_chorusflanger:tap_chorusflanger"



class TestLiveAudioPlayer(unittest.TestCase):
    
    def test_audio_filter_com(selponentf):
        TestModel = EffectPresets('test')
        plist = TestModel.getParamList('compressor')
        plist[0].value = 10
        plist[1].value = 10
        plist[2].value = -30
        plist[3].value = 36.48
        TestModel.getEnabledParam("compressor").value = True 

        tp = LiveAudioPlayer()

        
        _ffmpeg_effect(self, name, effect, model)
         
        
    
