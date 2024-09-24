#include "gcsynth.h"

void gcsynth_stop(struct gcsynth* gcSynth)
{
    if(gcSynth->adriver)
    {
        delete_fluid_audio_driver(gcSynth->adriver);
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
}
