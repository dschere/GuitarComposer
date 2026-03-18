#ifndef __GCSYNTH_FILTER_GRAPH_H__
#define __GCSYNTH_FILTER_GRAPH_H__

#include <glib.h>

#include "gcsynth.h"
#include "gcsynth_filter.h"

#ifndef AUDIO_SAMPLES
#define AUDIO_SAMPLES 64
#endif


























// Unused code to be used as reference for new code
// will be removed.

enum
{
    EFFECT_CHAIN_ALLPASS,
    EFFECT_CHAIN_LOWPASS,
    EFFECT_CHAIN_HIGHPASS,
    EFFECT_CHAIN_BANDPASS
};

// maximum filter chains per channel
#define MAX_FILTER_CHAINS 8

/**
+-------+                                          +--------------------+
+ input |----- demux (port 1) ---                 -| muxer              |--> output 
+  pre  +         balance                          |   chan balance     |
                  bandpass/highpass/lowpass        |   chan equalizer   |
               demux (port 2) ---                 -|
                  balance                          |
                  bandpass/highpass/lowpass        | 
               demux (port 3) ---                 -|    

pre: effects applied before demux such as compressor, noise gate etc.

*/


struct fg_effect_chain
{
    int chain_pass_type;
    float low_freq;
    float high_freq;
    float freq;
    int enabled;

    float balance;
    float gain;

    GList* effects;
    /**
     * Per frame: 
     * 
     * copy from gcsynth_filter_graph->input_left/right
     *   use optional band pass to determine if chain should be called.
     *   apply optional balance and gain
     * walk through effects applying effects to left/right
     * 
     * when finished left/right gets mixed using the demux  
     */
    int populated; // if 0 then left/right buffers were not populated
                   // they will be skipped by the muxer.   
    float  left[AUDIO_SAMPLES];
    float  right[AUDIO_SAMPLES];
};

struct fg_demux 
{
    int num_chains; // number of filter chains in use.
    struct fg_effect_chain effect_chains[MAX_FILTER_CHAINS];
};

struct gcsynth_filter_graph 
{
    float in_left[AUDIO_SAMPLES];
    float in_right[AUDIO_SAMPLES];
    float* out_left;
    float* out_right;

    GList* pre_demux_effects; // works in in_left/right prior to demux
    float balance; // out_left/right -1.0 all left, 1.0 all right
    float gain;    // default 1.0

    int enabled;

    int filter_enabled_count;

    struct fg_demux demuxer;
    // mux is a mixer function taking the dexumer left/right buffers and outputting
    // them to out_left/right while applying balance and gain.
};

// initialization
//void fg_init(struct gcsynth_filter_graph* fg);


// run the filter graph on the stereo audio data 
//void fg_run(struct gcsynth_filter_graph* fg, int channel, float* left, float* right);


void fg_enable(struct gcsynth_filter_graph* fg, int enabled);
 

// demux functions
void pre_demux_proc(struct gcsynth_filter_graph* fg, float* left, float* right);
void demux_proc(struct gcsynth_filter_graph* fg, int channel);

void fg_demux_enable_chain(struct gcsynth_filter_graph* fg, int chain_idx, int enable);
void fg_demux_num_chains(struct gcsynth_filter_graph* fg, int num_chains);
void fg_demux_chain_balance(struct gcsynth_filter_graph* fg, int chain_idx, float balance);
void fg_demux_chain_gain(struct gcsynth_filter_graph* fg, int chain_idx, float gain);

int fg_create_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    const char* pathname, 
    char* label 
);

int fg_remove_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    char* pathname
);

// allow fg_find_filter to return multiple variables.
struct fg_find_filter_result 
{
    GList** list; // this list where the item lives
    GList* iter; // the item within the list
    struct gcsynth_filter* filter; // the filter itself 
    int found;
};

// primitive that searches for a filter by label in a filter chain
// or pre demux filter. 
struct fg_find_filter_result fg_find_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    char* label
);


void fg_enable_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    char* label, int enable
);

int fg_demux_set_param_byindex(struct gcsynth_filter_graph* fg, int chain_idx,
    char* label, int pidx, float value);

int fg_demux_set_param_byname(struct gcsynth_filter_graph* fg, int chain_idx,
    char* label, char* name, float value);

// called mix audio from demuxer filter chains into left/right output. provided by fg_run   
void muxer_proc(struct gcsynth_filter_graph* fg);

// utility functions
void fg_proc_balance_gain(float balance, float gain, float* left, float* right);




//-----------------------------------------------------------

/*
   Since we are generating the input sound we can precalculate the 
   frequency domain so that we can do accurate filtering (high/low/band pass)
   without the use of expensive FFT.  
*/

// clear internal stats/buffers etc.

// defined in fgraph/freqdomain.c
void fg_freq_domain_event_clear(); 
void fg_freq_domain_event_add(int channel, float freq, float amp, float* left, float* right);

void midi_filter_created();
void midi_filter_destroyed();

float midi2freq(int midi_key);

int fg_bandpass_filter(int channel, float low, float high, float* left, float* right);
int fg_highpass_filter(int channel, float freq, float* left, float* right);
int fg_lowpass_filter(int channel, float freq, float* left, float* right);







#endif
