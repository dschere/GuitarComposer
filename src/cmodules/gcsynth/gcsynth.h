#ifndef __GCSYNTH_H
#define __GCSYNTH_H

// I am using my modified fluidsynth
#include "../../../include/fluidsynth.h"
#include "ladspa.h"

#include "gcsynth_channel.h"

#define MAX_SOUNDFONTS 255
#define ERRMSG_SIZE 4096

#define NUM_CHANNELS 32
#define MAX_CHANNELS 64

enum {
    NOWARNING,

    FILTER_CONTROL_NO_FOUND,
    FILTER_CONTROL_VALUE_ABOVE_BOUNDS,
    FILTER_CONTROL_VALUE_BELOW_BOUNDS,
    
    NUM_WARNINGS
};

struct gcsynth_cfg {
    int test; // running in test only mode?
    int num_sfpaths;
    char* sfpaths[MAX_SOUNDFONTS]; // NULL sentinel value terminates list  
    int num_midi_channels;
};



struct gcsynth {
    fluid_synth_t*        synth;
    fluid_settings_t*     settings;
    fluid_audio_driver_t* adriver;


    struct gcsynth_cfg cfg;
    //PerChannelFxFuncType callback;
};

void gcsynth_start(struct gcsynth* gcSynth);
void gcsynth_stop(struct gcsynth* gcSynth);


void gcsynth_raise_exception(char* text);



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