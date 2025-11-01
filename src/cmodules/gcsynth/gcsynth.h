#ifndef __GCSYNTH_H
#define __GCSYNTH_H

#include "ladspa.h"

#include "gcsynth_channel.h"

#define MAX_SOUNDFONTS 255
#define ERRMSG_SIZE 4096

#define NUM_CHANNELS 64
#define LIVE_CAPTURE_CHANNEL NUM_CHANNELS-1 

// +/- 12 semitones
#define PITCH_WHEEL_SENSITIVITY 12

//#define AUDIO_SAMPLES 64*64
#define AUDIO_SAMPLES 64
#define SAMPLE_RATE  44100 

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
    short synth_destination, client_destination;

    struct gcsynth_cfg cfg;
    //PerChannelFxFuncType callback;
};

void gcsynth_start(struct gcsynth* gcSynth);
void gcsynth_stop(struct gcsynth* gcSynth);


void gcsynth_raise_exception(char* text);

// switched on/off by environment variable GCSYNTH_DEBUG_TIMINGLOG=1
// if so then the log will be created in /tmp/gcsynth_timing.log
#define TIMING_LOGPATH "/tmp/gcsynth_timing.log"
#define TIMING_LOG_ENV "GCSYNTH_DEBUG_TIMINGLOG"
void timing_log(char* caller, char *method);


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