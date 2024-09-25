#include <string.h>
#include "gcsynth.h"

#include "gcsynth_channel.h"
#include "gcsynth_filter.h"


static struct gcsynth_channel ChannelFilters[MAX_CHANNELS]; 


static struct gcsynth_filter* find_by_name(
    struct gcsynth_channel* c, char* plugin_name);  


int gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_name)
{
    struct gcsynth_channel *c = &ChannelFilters[channel]; // gcsynth.c validated channel
    char errmsg[256];

    // check for duplicate 
    if (find_by_name(c,plugin_name) != NULL) {
        sprintf(errmsg,"gcsynth_channel_add_filter duplicate plugin name %s not allowed!", plugin_name);
        gcsynth_raise_exception(errmsg);
        return -1;
    }

    // create a filter and add it to the filter chain

    return 0;
}

int gcsynth_channel_set_control_by_index(int channel,
    char* plugin_name, int control_num, float value)
{
    return 0;
}

int gcsynth_channel_set_control_by_name(int channel,
    char* plugin_name, char* control_name, float value)
{
    return 0;
}




void voice_data_router(void *userdata, int chan, double* buf, int len)
{
    // dequeue any/all user changes to a filter chain.

    // run a filter chain for a channel if one exists 
}



// private helper routines



static struct gcsynth_filter* find_by_name(
    struct gcsynth_channel* c, char* plugin_name)
{
    GList* iter;
    
    for(iter = g_list_first(c->filter_chain);
        iter != NULL;
        iter = iter->next
    ) {
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
        if (strcmp(f->desc->Label,plugin_name) == 0) {
            return f;
        }
    }
    return NULL;
}
 












