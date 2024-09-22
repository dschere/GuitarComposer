#ifndef __GCSYNTH_H
#define __GCSYNTH_H

#include <glib.h>

// I am using my modified fluidsynth
#include "../../../include/fluidsynth.h"
#include "ladspa.h"

#define MAX_SOUNDFONTS 255
#define ERRMSG_SIZE 4096

struct gcsynth_start_cfg {
    int test; // running in test only mode?
    int num_sfpaths;
    char* sfpaths[MAX_SOUNDFONTS]; // NULL sentinel value terminates list  
};



struct gcsynth {
    fluid_synth_t*        synth;
    fluid_settings_t*     settings;
    fluid_audio_driver_t* adriver;


    // interthread communication between python and fluidsynth 
    GQueue* msgq; // needed to make audio effects filter changes 
                  // while channels are being used for inflight
                  // parameter changes.   

    //PerChannelFxFuncType callback;
};

void gcsynth_start(struct gcsynth* gcSynth, struct gcsynth_start_cfg* cfg);
void gcsynth_stop(struct gcsynth* gcSynth);


void gcsynth_raise_exception(char* text);


void voice_data_router(void *userdata, int chan, double* buf, int len);


/**
 * python api
 * 
 * // create synth and load soundfont files, the index
 * // of sfpaths + 1 is the id number of the sound font
 * // for reference in the select command
 * gcsynth.start({"sfpaths":[..list of sf files..]})
 * 
 */

#endif