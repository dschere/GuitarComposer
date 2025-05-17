#include <unistd.h>
#include <unistd.h>

#include "gcsynth.h"
#include "gcsynth_event.h"
#include "gcsynth_sf.h"
#include "gcsynth_channel.h"


void gcsynth_start(struct gcsynth* gcSynth)
{
#define RAISE(errmsg) { gcsynth_raise_exception(errmsg); gcsynth_stop(gcSynth); return; }   
    int i;
    char errmsg[4096];
    struct gcsynth_cfg* cfg = &gcSynth->cfg;

    // check for existance of soundfont files 
    for(i = 0; i < cfg->num_sfpaths; i++) {
        if (access(cfg->sfpaths[i],F_OK) != 0) {
            sprintf(errmsg,"Soundfont file (%s) not found!",cfg->sfpaths[i]);
            RAISE(errmsg)
        }
    }

    // new synth
    if (gcsynth_sf_init(cfg->sfpaths, cfg->num_sfpaths, synth_filter_router)) {
        RAISE("unable to launch synth")
    }


    gcsynth_sequencer_setup(gcSynth);

    //gcSynth->settings = NULL;
    // gcSynth->synth = NULL;
    // gcSynth->adriver = NULL;

    // if ((gcSynth->settings = new_fluid_settings()) != NULL) {
    //     // use alsa for output
    //     r = fluid_settings_setstr(gcSynth->settings, "audio.driver", "alsa");
    //     if (r != FLUID_OK) RAISE("fluid_settings_setstr: Unable to set audio.driver");

        
    //     r = fluid_settings_setint(gcSynth->settings,"synth.midi-channels", cfg->num_midi_channels);
    //     if (r != FLUID_OK) {
    //         sprintf(errmsg,"fluid_settings_setnum: Unable to set synth.midi-channels to %d", cfg->num_midi_channels);
    //         RAISE(errmsg);
    //     }
        
    //     if ((gcSynth->synth = new_fluid_synth(gcSynth->settings)) != NULL) {
    //         // load sound fonts into synthesizer
    //         for(i = 0; i < cfg->num_sfpaths; i++) {
    //             if (fluid_synth_sfload(gcSynth->synth, 
    //                 cfg->sfpaths[i], 1) == -1) {

    //                 sprintf(errmsg,"fluid_synth_sfload failed to load %s",cfg->sfpaths[i]);
    //                 RAISE(errmsg)
    //             } 
    //         } 

    //         // create audio driver
    //         gcSynth->adriver = new_fluid_audio_driver(
    //             gcSynth->settings, gcSynth->synth);

    //         // install the channel data router 
    //         fluid_synth_set_user_per_channel_fx_func(
    //             gcSynth->synth, voice_data_router, gcSynth);

    //         fluid_synth_set_gain(gcSynth->synth, 1.0);

    //         gcsynth_sequencer_setup(gcSynth);

    //         // set defaults for each channel
    //         for(i = 0; i < cfg->num_midi_channels; i++) {
    //             fluid_synth_pitch_wheel_sens(gcSynth->synth, 
    //                 i, PITCH_WHEEL_SENSITIVITY);
    //         }

    //         // set state  
    //         gcsynth_update_state_when_started();

    //         // ready to rock and roll    
    //         printf("fluidsynth started!\n");
    //     } else {
    //         RAISE("new_fluid_synth failed!")
    //     }
    // } else {
    //     RAISE("new_fluid_settings failed, unable to start synth!")
    // }
}

