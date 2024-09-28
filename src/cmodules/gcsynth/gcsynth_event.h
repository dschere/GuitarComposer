#ifndef __GCSYNTH_EVENT_H
#define __GCSYNTH_EVENT_H

#include "gcsynth.h"


void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity);
void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode);
void gcsynth_select(struct gcsynth* gcs, int chan,  int sfont_id, int bank_num, int preset_num);

#endif