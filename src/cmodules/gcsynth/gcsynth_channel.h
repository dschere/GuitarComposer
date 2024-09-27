#ifndef GCSYNTH_CHANNEL_H
#define GCSYNTH_CHANNEL_H


#include <glib.h>

struct gcsynth_channel {
    // filter chain  
    GList* filter_chain;
    GMutex mutex;
    int initialized;
};

//Note channel has already been range checked prior to these function calls.

// load the plugin and assign an instance of the plugin to a filter chain associated
// with a channel.
int gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_label);
int gcsynth_channel_remove_filter(int channel, char* plugin_label_or_all);

int gcsynth_channel_set_control_by_index(int channel, char* plugin_label, 
    int control_num, float value);
int gcsynth_channel_set_control_by_name(int channel, char* plugin_label, 
    char* control_name, float value);

// main entry point from fluidsynth to route synth voice data into 
// an audio filter chain.
void voice_data_router(void *userdata, int chan, double* buf, int len);


#endif