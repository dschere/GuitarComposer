#include "gcsynth.h"

void gcsynth_stop(struct gcsynth* gcSynth)
{
    gcsynth_update_state_when_stopped();
    
    // note: sequence of shutdown is important.
    if(gcSynth->adriver)
    {
        delete_fluid_audio_driver(gcSynth->adriver);
    }

    if (gcSynth->sequencer) {
        delete_fluid_sequencer(gcSynth->sequencer);
    }

    if(gcSynth->synth)
    {
        delete_fluid_synth(gcSynth->synth);
    }
 
    if(gcSynth->settings)
    {
        delete_fluid_settings(gcSynth->settings);
    }


    gcSynth->adriver = NULL;
    gcSynth->synth = NULL;
    gcSynth->settings = NULL;
    gcSynth->sequencer = NULL;
}
