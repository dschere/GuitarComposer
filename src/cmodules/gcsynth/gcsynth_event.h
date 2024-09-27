#ifndef __GCSYNTH_EVENT_H
#define __GCSYNTH_EVENT_H

#include "gcsynth.h"


void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity);
void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode);


#endif