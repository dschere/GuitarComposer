#include <unistd.h>
#include <unistd.h>

#include "gcsynth.h"

void gcsynth_start(struct gcsynth* gcSynth)
{
#define RAISE(errmsg) { gcsynth_raise_exception(errmsg); gcsynth_stop(gcSynth); return; }   
    int i;
    char errmsg[4096];
    int r;
    struct gcsynth_cfg* cfg = &gcSynth->cfg;

    // check for existance of soundfont files 
    for(i = 0; i < cfg->num_sfpaths; i++) {
        if (access(cfg->sfpaths[i],F_OK) != 0) {
            sprintf(errmsg,"Soundfont file (%s) not found!",cfg->sfpaths[i]);
            RAISE(errmsg)
        }
    }

    gcSynth->settings = NULL;
    gcSynth->synth = NULL;
    gcSynth->adriver = NULL;

    if ((gcSynth->settings = new_fluid_settings()) != NULL) {
        // use alsa for output
        r = fluid_settings_setstr(gcSynth->settings, "audio.driver", "alsa");
        if (r != FLUID_OK) RAISE("fluid_settings_setstr: Unable to set audio.driver");

        r = fluid_settings_setint(gcSynth->settings,"synth.midi-channels", cfg->num_midi_channels);
        if (r != FLUID_OK) {
            sprintf(errmsg,"fluid_settings_setnum: Unable to set synth.midi-channels to %d", cfg->num_midi_channels);
            RAISE(errmsg);
        }
        
        if ((gcSynth->synth = new_fluid_synth(gcSynth->settings)) != NULL) {
            // load sound fonts into synthesizer
            for(i = 0; i < cfg->num_sfpaths; i++) {
                if (fluid_synth_sfload(gcSynth->synth, 
                    cfg->sfpaths[i], 1) == -1) {

                    sprintf(errmsg,"fluid_synth_sfload failed to load %s",cfg->sfpaths[i]);
                    RAISE(errmsg)
                } 
            } 
            // install the channel data router 
            fluid_synth_set_user_per_channel_fx_func(
                gcSynth->synth, voice_data_router, gcSynth);
            // ready to rock and roll    
        } else {
            RAISE("new_fluid_synth failed!")
        }
    } else {
        RAISE("new_fluid_settings failed, unable to start synth!")
    }
}
