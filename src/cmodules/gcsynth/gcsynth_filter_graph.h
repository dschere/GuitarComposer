#ifndef __GCSYNTH_FILTER_GRAPH_H__
#define __GCSYNTH_FILTER_GRAPH_H__

#include <glib.h>

#include "gcsynth.h"
#include "gcsynth_filter.h"


enum 
{
    FGO_NODE,
    FGO_EDGE,
    FGO_INPUT,
    FGO_OUTPUT,

    FGO_GRAPH
};

#define UUID_LENGTH 36

struct fg_object
{
    char uuid[UUID_LENGTH+1];
    int id;
    int otype;
};

struct fg_io
{
    struct fg_object base;
    float left[AUDIO_SAMPLES];
    float right[AUDIO_SAMPLES];
};

struct fg_node
{
    struct fg_object base;
    struct gcsynth_filter* filter;
};


struct fg_edge 
{
    struct fg_object base;
    int num_outputs;
    struct fg_object* outputs;
    struct gcsynth_filter* filter;
};


/**
 * Manages a graph of filters, each graph has two inputs left/right audio and two
 * outpus left/right
 * 
 */
struct gcsynth_filter_graph 
{
    struct fg_object base; // FGO_GRAPH
    GList* node_list;
    GList* edges;

    struct fg_io input, output;
};

/**
 * graph filter api 
 *    The application supplies uuid's that are used to 
 *  tag various objects created. Once assigned and configured 
 *  it is assigned to a channel which will send a message to 
 *  audio rendering thread to assign teh graph to process audio
 *  for that channel.
 *  
 *  Real time chanes can be made by sending subsiquent messages 
 *  that can alter effects parameters and activate deactivate them
 *  
 */

struct fg_param_cfg 
{
    char* graph_uuid;
    char* filter_uuid;
    char* filename;
    char* label;
    char* param_name;
    float value;
};

struct fg_connect_args
{
    char* graph_uuid;
    char* connector_uuid;
    
    char* input_uuid;
    char* output_uuid;
    int using_midi;
    
    int is_low_pass;
    float low_pass_freq;

    int is_high_pass;
    float high_pass_freq;
};



int fg_create(char* graph_uuid);
int fg_unassign(char* graph_uuid, int channel);
// also acts as a replace unassign then assign new.
int fg_assign(char* graph_uuid, int channel);
// must be unassigned or else this will error
int fg_destroy(char* graph_uuid);

int fg_add_filter(struct fg_param_cfg* param);
int fg_update_filter_param(struct fg_param_cfg* param);
int fg_activate_filter(struct fg_param_cfg* param);
int fg_deactivate_filter(struct fg_param_cfg* param);

/**
 * Create a connection or a splitter if called repeatedly with 
 * the same input.
 * 
 * In the case of a connection only one call will connect an input to
 * an output.
 * 
 * Calling this repeatedly with the same input but different outputs creates
 * a one to many splitter. Extra args such as low/high pass sets the conditions
 * in which the input is sent to the output. If no conditions then this simply
 * copies the input to multiple outputs.
 * 
 */
int fg_connect(struct fg_connect_args* args);


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






#endif
