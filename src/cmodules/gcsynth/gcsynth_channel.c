#include <string.h>
#include <math.h>

#include "gcsynth.h"

#include "gcsynth_channel.h"
#include "gcsynth_filter.h"


static struct gcsynth_channel ChannelFilters[MAX_CHANNELS]; 

static struct gcsynth_filter* find_by_name(
    struct gcsynth_channel* c, char* plugin_label);  
static int update_ctrl_val(struct gcsynth_filter_control* control, float value);

static int _gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_label);
static int _gcsynth_channel_remove_filter(int channel, char* plugin_label);

static int _gcsynth_channel_set_control_by_index(int channel, char* plugin_label, 
    int control_num, float value);
static int _gcsynth_channel_set_control_by_name(int channel, char* plugin_label, 
    char* control_name, float value);
static void _voice_data_router(void *userdata, int chan, double* buf, int len);

static void lock_channel(int channel);
static void unlock_channel(int channel);



int gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_label)
{
    int ret;

    lock_channel(channel);
    ret = _gcsynth_channel_add_filter(channel, filepath, plugin_label);    
    unlock_channel(channel);

    return ret;
}

int gcsynth_channel_remove_filter(int channel, char* plugin_label)
{
    int ret;

    lock_channel(channel);
    ret = _gcsynth_channel_remove_filter(channel, plugin_label);
    unlock_channel(channel);

    return ret;
}

void gcsynth_remove_all_filters()
{
    int channel;
    for(channel = 0; channel < MAX_CHANNELS; channel++) {
        gcsynth_channel_remove_filter(channel, NULL);
    }
}


int gcsynth_channel_set_control_by_index(int channel, char* plugin_label, 
    int control_num, float value)
{
    int ret;
    lock_channel(channel);
    ret = _gcsynth_channel_set_control_by_index(channel,plugin_label, 
         control_num, value);
    unlock_channel(channel);
    return ret;
}   

int gcsynth_channel_set_control_by_name(int channel, char* plugin_label, 
    char* control_name, float value)
{
    int ret;
    lock_channel(channel);
    ret = _gcsynth_channel_set_control_by_name(channel, plugin_label, 
         control_name, value);
    unlock_channel(channel);
    return ret;
}    

// -- fluidsynth interface for applying a filterchain to a voice ----
// 
void voice_data_router(void *userdata, int chan, double* buf, int len)
{
//printf("voice_data_router chan=%d len=%d\n", chan, len);    
    if ((chan >= 0) && (chan < MAX_CHANNELS)) {
        lock_channel(chan);
        _voice_data_router(userdata, chan, buf, len);
        unlock_channel(chan);
    }
}
//////////////////////////////////////////////////////////////////////




// --- static functions

static void lock_channel(int channel)
{
    struct gcsynth_channel* c = &ChannelFilters[channel];

    if (c->initialized == 0) {
        g_mutex_init(&c->mutex);
        c->initialized = 1;
    }
    g_mutex_lock(&c->mutex);    
}

static void unlock_channel(int channel)
{
    struct gcsynth_channel* c = &ChannelFilters[channel];
    g_mutex_unlock(&c->mutex);    
}



static void _voice_data_router(void *userdata, int chan, double* buf, int len)
{
    int i;
    LADSPA_Data fc_buffer[FLUID_BUFSIZE];
    GList* iter;

    
    // len is always 
    struct gcsynth_channel *c = &ChannelFilters[chan];
    if (c->filter_chain != NULL) {
        
        // copy the voice buffer from fluid synth (double) to the ladspa buffer (float)
        for(i = 0; i < len && i < FLUID_BUFSIZE; i++) fc_buffer[i] = buf[i];

        // walk through the filter chain
        for(iter = g_list_first(c->filter_chain);
            iter != NULL;
            iter = iter->next
        ) {
            struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
            // continuously overwrite fc_buffer for each enabled filter
            gcsynth_filter_run(f, fc_buffer, len);
        }

        // output fc_buffer to the fluidsynth buffer
        for(i = 0; i < len && i < FLUID_BUFSIZE; i++) buf[i] = fc_buffer[i];
    } 
}





static int _gcsynth_channel_remove_filter(int channel, char* plugin_label_or_all)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel

   // Iterate through the list and delete a specific item
    GList *iter = c->filter_chain;
    while (iter != NULL) {
        GList *next = iter->next;  // Save the next pointer before potential deletion
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;

        if (plugin_label_or_all == NULL) {
            gcsynth_filter_destroy(f);
            // unlink from double linked list.
            c->filter_chain = g_list_delete_link(c->filter_chain, iter);
        }
        else if (strcmp(f->desc->Label,plugin_label_or_all) == 0) {
            // deallocate
            gcsynth_filter_destroy(f);
            // unlink from double linked list.
            c->filter_chain = g_list_delete_link(c->filter_chain, iter);
            break;
        }

        iter = next;  // Move to the next item in the list
    }

    return 0;
}


static int _gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_label)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel
    char errmsg[256];
    struct gcsynth_filter* f;

    // check for duplicate 
    if (find_by_name(c,plugin_label) != NULL) {
        sprintf(errmsg,"gcsynth_channel_add_filter duplicate plugin name %s not allowed!", plugin_label);
        gcsynth_raise_exception(errmsg);
        return -1;
    }

    // create a filter and add it to the filter chain
    if ((f = gcsynth_filter_new_ladspa(filepath, plugin_label)) == NULL) {
        // exception already set, just return
        return -1;
    }
    
    // start with filter disabled as the default state.
    f->enabled = 0;
    f->frame_count = 0;

    // add to the filter chain
    c->filter_chain = g_list_append(c->filter_chain, f);

    return 0;
}

static int _gcsynth_channel_set_control_by_index(int channel,
    char* plugin_label, int control_num, float value)
{
    int ret = FILTER_CONTROL_NO_FOUND; 
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel
    struct gcsynth_filter* f = find_by_name(c,plugin_label);
    struct gcsynth_filter_control* control;

    // control_num

    if (f && control_num < f->num_controls && control_num >= 0) {
        control = &f->controls[control_num];
        ret = update_ctrl_val(control, value);
    }

    return ret;
}

static int _gcsynth_channel_set_control_by_name(int channel,
    char* plugin_label, char* control_name, float value)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel
    struct gcsynth_filter* f = find_by_name(c,plugin_label);
    int i;
    int ret = FILTER_CONTROL_NO_FOUND;

    if (f) {
        for(i = 0; i < f->num_controls; i++) {
            if (strcmp(f->controls[i].name,control_name) == 0) {
                ret = update_ctrl_val(&f->controls[i], value); 
                break;
            }
        } 
    }

    return ret;
}




static int update_ctrl_val(struct gcsynth_filter_control* control, float value)
{
    int ret = NOWARNING;

    if (control->is_toggled) {
        control->value = (value != 0.0) ? 1.0: 0.0; 
    } else {
        if (control->is_bounded_above && value > control->upper) {
            ret = FILTER_CONTROL_VALUE_ABOVE_BOUNDS; // failed upper bounds check
        }
        else if (control->is_bounded_below && value < control->lower) {
            ret = FILTER_CONTROL_VALUE_BELOW_BOUNDS; // failed lower bounds check
        } else {
            // value is is in range
            if (control->is_integer) {
                control->value = ceil(value);
            } else {
                control->value = value;
            }
        }
    }

    return ret;
}


static struct gcsynth_filter* find_by_name(
    struct gcsynth_channel* c, char* plugin_label)
{
    GList* iter;
    
    for(iter = g_list_first(c->filter_chain);
        iter != NULL;
        iter = iter->next
    ) {
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
        if (strcmp(f->desc->Label,plugin_label) == 0) {
            return f;
        }
    }
    return NULL;
}
 












