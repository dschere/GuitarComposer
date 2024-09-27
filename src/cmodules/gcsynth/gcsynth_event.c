#include "gcsynth_event.h"

void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity)
{
    fluid_synth_noteon(gcs->synth, chan, midicode, velocity);
}


void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode)
{
    fluid_synth_noteoff(gcs->synth, chan, midicode);
}
