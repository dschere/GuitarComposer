#ifndef __FGRAPH_H__
#define __FGRAPH_H__

#include <glib.h>

#include "../gcsynth.h"
#include "../gcsynth_filter.h"

#define UUID_LEN 37

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


enum 
{
    FG_CONNECTION, 

    FG_LOW_PASS,
    FG_HIGH_PASS,
    FG_BAND_PASS,
    FG_EFFECT,
    FG_INPUT,
    FG_OUTPUT,
    FG_MIXER,
    FG_SPLITTER,
    FG_GAIN_BALANCE,
    FG_GRAPH,

    NUM_FG_ENTITY_TYPES
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

    void (*run)(struct fgraph_node* node, float* left, float* right);
    
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

    struct fgraph_node *in_node; 
    struct fgraph_node *out_node;
};


struct fgraph
{
    int enabled;
    struct fgraph_base base;
    struct fgraph_connection 
        *input_node, 
        *output_node
    ;

    GHashTable* nodes;       // uuid -> struct fg_node_* 
    GHashTable* connections; // uuid -> struct fg_connection 
};

// initialize global resources for supporting audio filter graphs.
int fg_init();

// create and destroy a filter graph
void fg_create(char* uuid);
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


// control ladspa ports
int fg_set_effect_property(char* fg_uuid, char* node_uuid, char* property, float value);
// set not attributes (enabled etc.)

int fg_set_node_attribute(char* node_uuid, int type, 
    int att_id, int ival, float fval,  char* sval);

#endif //__FGRAPH_H__