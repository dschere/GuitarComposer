#ifndef __GCSYNTH_FILTER_H
#define __GCSYNTH_FILTER_H

#include "gcsynth.h"

#ifndef FLUID_BUFSIZE
#define FLUID_BUFSIZE 64
#endif

#define MAX_LADSPA_CONTROLS 32
#define MAX_LADSPA_PORTS    MAX_LADSPA_CONTROLS + 4

//make this adjustable? although I've never seen the need
#define SAMPLE_RATE 44100

struct gcsynth_filter_control {
    int isOutput;
    int has_default;
    LADSPA_Data default_value;

    const char* name;
    LADSPA_Data value; // memory shared with plugin

    // characteristics of the value
    int is_bounded_below;
    int is_bounded_above;
    int is_toggled;
    int is_integer;
    int is_logarithmic;

    LADSPA_Data lower, upper;
};

enum {
    PORTMAP_LEFT,
    PORTMAP_RIGHT,

    NUM_IO_PORTMAPS
};

struct gcsynth_filter {
    void* dl_handle;

    int enabled;

    const LADSPA_Descriptor* desc;
    LADSPA_Descriptor_Function descriptor_fn;
    LADSPA_Handle* plugin_instance;

    unsigned long int frame_count;

    int num_controls;
    struct gcsynth_filter_control controls[MAX_LADSPA_CONTROLS];

    int in_buf_count;
    int out_buf_count;
    LADSPA_Data in_data_buffer[NUM_IO_PORTMAPS][FLUID_BUFSIZE];
    LADSPA_Data out_data_buffer[NUM_IO_PORTMAPS][FLUID_BUFSIZE];

    // port maps
    //  port number -> buffer
    LADSPA_Data* port_map[MAX_LADSPA_PORTS];
};



// loads a filter using ladspa, perhaps in the future this will
// be extended, on error NULL is returned and GcsynthException is raised.
struct gcsynth_filter* gcsynth_filter_new_ladspa(const char* pathname, char* label);

// free all resources, the memory itself is freed so 'gc_filter' is
// no longer usable after this call. 
void gcsynth_filter_destroy(struct gcsynth_filter* gc_filter);

// sets the value of a control
//int gcsynth_filter_setbyname(struct gcsynth_filter* gc_filter, char* name, LADSPA_Data value);
//int gcsynth_filter_setbyindex(struct gcsynth_filter* gc_filter, int, LADSPA_Data value);

// sends FLUID_BUFSIZE size to the filter and copies FLUID_BUFSIZE out from the
// filter 
int gcsynth_filter_run(struct gcsynth_filter* gc_filter, LADSPA_Data* io_buf, int len);



void gcsynth_filter_enable(struct gcsynth_filter* gc_filter);
void gcsynth_filter_disable(struct gcsynth_filter* gc_filter);
int  gcsynth_filter_isEnabled(struct gcsynth_filter* gc_filter);



#endif