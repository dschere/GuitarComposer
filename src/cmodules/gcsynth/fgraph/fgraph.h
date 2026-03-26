#ifndef __FGRAPH_H__
#define __FGRAPH_H__

#include <glib.h>

#include "../gcsynth.h"
#include "../gcsynth_filter.h"

#define UUID_LEN 37

#ifndef AUDIO_SAMPLES
#define AUDIO_SAMPLES 64
#endif

struct fgraph_node;
struct fgraph_bandpass;
struct fgraph_effect;
struct fgraph_highpass;
struct fgraph_lowpass;
struct fgraph_base; // mixer and splitter are just configurations.


// In the case for a live channel we can't use the buffers
// in freqdomain that already have audio buffers associated with
// frequency, in this case the band/low/high pass filters will
// use a ladspa module, since the frequancy domain needs to be calculated.
#define FALLBACK_LOWPASS_FILTER_DEF_NAME "lowpass_iir"
#define FALLBACK_LOWPASS_FILTER_DEF_PATH "/usr/lib/ladspa/lowpass_iir_1891.so"
#define FALLBACK_HIGHPASS_FILTER_NAME    "highpass_iir"
#define FALLBACK_HIGHASS_FILTER_DEF_PATH "/usr/lib/ladspa/highpass_iir_1890.so"

#define FG_CONNECTION 100
#define FG_GRAPH 101

enum  {
    FG_NODE_TYPE_LOWPASS,
    FG_NODE_TYPE_HIGHPASS,
    FG_NODE_TYPE_BANDPASS,
    FG_NODE_TYPE_EFFECT,
    FG_NODE_TYPE_INPUT,
    FG_NODE_TYPE_OUTPUT,
    FG_NODE_TYPE_MIXER,
    FG_NODE_TYPE_SPLITTER,
    FG_NODE_TYPE_GAIN_BALANCE,

    FGRAPH_NUM_NODE_TYPES
};


enum 
{
    AID_ENABLE_FALLBACK_METHOD,
    AID_DISABLE_FALLBACK_METHOD,
    AID_GAIN,
    AID_BALANCE,
    AID_LOW_PASS_FREQ,
    AID_HIGH_PASS_FREQ,
    AID_BAND_PASS_LOW_FREQ,
    AID_BAND_PASS_HIGH_FREQ,
    AID_ENABLE,
    AID_DISABLE,



    NUM_NODE_ATTR_IDS
};

struct fgraph_base 
{
    int type;
    char uuid[UUID_LEN];
};


struct fgraph_node
{
    struct fgraph_base base;

    int enabled;
    GList* in_ports; // list of fgraph_connections for inputs
    GList* out_ports; // list of fgraph_connections for inputs
    
    // if set to true then iir filters are used not precalculated buffers.
    int using_fallback_method_for_freqdomain;

    int (*run)(struct fgraph_node* node, float* left, float* right);

    // incremented every time an input/output port connection has had its
    // left/right buffers populated. Using modulo math we can determine when 
    // all ports are about to be filled.
    unsigned long in_port_update_count; 
    unsigned long out_port_update_count;

    // book keeping variables used for audio processing.

    int channel; // channel assigned to audio
};


 

struct fgraph_lowpass 
{
    struct fgraph_node node;

    float freq;
    struct gcsynth_filter* fallback_lowpass;
};

struct fgraph_highpass 
{
    struct fgraph_node node;

    float freq;
    struct gcsynth_filter* fallback_highpass;
};

struct fgraph_bandpass 
{
    struct fgraph_node node;

    float freq_low;
    float freq_high;

    struct gcsynth_filter* fallback_highpass;
    struct gcsynth_filter* fallback_lowpass;
};

struct fgraph_effect 
{
    struct fgraph_node node;

    struct gcsynth_filter* filter;
};

struct fgraph_gain_balance
{
    struct fgraph_node node;

    float gain;
    float balance;
};


struct fgraph_connection 
{
    struct fgraph_base base;

    char uuid_in[UUID_LEN];
    int port_in;
    char uuid_out[UUID_LEN];
    int port_out;

    float left[AUDIO_SAMPLES];
    float right[AUDIO_SAMPLES];

    struct fgraph_node *in_node; 
    struct fgraph_node *out_node;
};


struct fgraph
{
    struct fgraph_base base;
 
 
    struct fgraph_node 
        *input_node, 
        *output_node
    ;

    GHashTable* nodes;       // uuid -> struct fg_node_* 
    GHashTable* connections; // uuid -> struct fg_connection 
    int enabled;

};

// initialize global resources for supporting audio filter graphs.
int fg_init();

struct fgraph_node* fg_lookup_node(struct fgraph* fg, char* uuid);
struct fgraph_connection* fg_lookup_connection(struct fgraph* fg, char* uuid);

// create and destroy a filter graph
void fg_create(char* uuid);
void fg_destroy(char* uuid);

void fg_api_destroy(char* uuid);
//TODO enable and disable of filter graph and connecting this to the py_module.

// lookup a filter fraph object, the caller will then cast the pointer 
// to a specific type. If expected_type == -1 then it is ignored.
struct fgraph_base* lookup_fgraph_object(char* uuid, int expected_type);

// create a node within a graph.
int fg_create_node(char* fg_uuid, char* node_uuid, int node_type);
int fg_delete_node(char* fg_uuid, char* node_uuid);
void fg_set_enable(char* uuid, int enabled);

// create/delete a connection of nodes
int fg_connect_nodes(char* fg_uuid, char* conn_uuid, 
    char* node1_uuid, int port1, char* node2_uuid, int port2);
int fg_delete_connection(char* fg_uuid, char* conn_uuid);

int assign_fg_to_channel(char* fg_uuid, int channel);
int unassign_fg_to_channel(int channel);



// control ladspa ports
int fg_set_effect_property(char* fg_uuid, char* node_uuid, char* property, float value);
int fg_setup_effect(char* fg_uuid, char* node_uuid, char* path, char* label);

// set not attributes (enabled etc.)

int fg_set_node_attribute(char* graph_uuid, char* node_uuid, int type,
    int att_id, int ival, float fval,  char* sval);


// process a filter graph and overwrite the left/right buffers with the output.
// both left and right buffers are AUDIO_SAMPLES (64) in length.    
void fg_run(struct fgraph* fg, int channel, float* left, float* right);

void fg_dump(struct fgraph* fg);
char* node_type_to_str(struct fgraph_node* n);

#endif //__FGRAPH_H__