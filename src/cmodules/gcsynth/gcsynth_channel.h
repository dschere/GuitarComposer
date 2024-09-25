#ifndef GCSYNTH_CHANNEL_H
#define GCSYNTH_CHANNEL_H


#include <glib.h>

struct gcsynth_channel {
    int enabled;
    GQueue* msgq; // update filter settings.
    // filter chain  
    GList* filter_chain;
};

//Note channel has already been range checked prior to these function calls.

// load the plugin and assign an instance of the plugin to a filter chain associated
// with a channel.
int gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_name);

int gcsynth_channel_set_control_by_index(int channel, char* plugin_name, 
    int control_num, float value);
int gcsynth_channel_set_control_by_name(int channel, char* plugin_name, 
    char* control_name, float value);


// main entry point from fluidsynth to route synth voice data into 
// an audio filter chain.
void voice_data_router(void *userdata, int chan, double* buf, int len);


#endif