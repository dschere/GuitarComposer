#include <string.h>
#include <math.h>

#include "gcsynth.h"

#include "gcsynth_channel.h"
#include "gcsynth_filter.h"
#include "gcsynth_sf.h"


static struct gcsynth_channel ChannelFilters[NUM_CHANNELS];


static GMutex StateMutex;
static int    StateMutexInitialized;
static int    GcsynthIdCount = 0;
static struct gcsynth_active_state GcsynthState;


static struct gcsynth_filter* find_by_name(
    struct gcsynth_channel* c, char* plugin_label);  

static int _gcsynth_channel_add_filter(int channel, const char* filepath, char* plugin_label);
static int _gcsynth_channel_remove_filter(int channel, char* plugin_label);

static int _gcsynth_channel_set_control_by_index(int channel, char* plugin_label, 
    int control_num, float value);
static int _gcsynth_channel_set_control_by_name(int channel, char* plugin_label, 
    char* control_name, float value);

static struct gcsynth_channel* lock_channel(int channel);
static void unlock_channel(int channel);

static void set_channel_state(int channel, char* plugin_label, int enabled);

void gcsynth_channel_gain(int channel, float gain)
{
    lock_channel(channel);
    ChannelFilters[channel].gain = gain;
    unlock_channel(channel);
}


void gcsynth_channel_enable_filter(int channel, char* plugin_label)
{
    lock_channel(channel);
    set_channel_state(channel, plugin_label,1);
    unlock_channel(channel);
}

void gcsynth_channel_disable_filter(int channel, char* plugin_label)
{
    lock_channel(channel);
    set_channel_state(channel, plugin_label,0);
    unlock_channel(channel);
}


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
    for(channel = 0; channel < NUM_CHANNELS; channel++) {
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



void synth_filter_router(int chan, float* left, float* right, int samples)
{
    GList* iter;
    struct gcsynth_channel *c = lock_channel(chan);
    int i;

    if (c) {        
        if (c->gain != 0.0) {
            for(i = 0; i < samples; i++) {
                left[i]  *= (1.0 + c->gain);
                right[i] *= (1.0 + c->gain);
            }
        }

        for(iter = g_list_first(c->filter_chain);
            iter != NULL;
            iter = iter->next
        ) {
            struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;

            // apply filter to audio buffers
            if (f->enabled) {
                gcsynth_filter_run_sterio(f, left, right, samples);
            }
        }
        unlock_channel(chan);
    }
}

float *synth_get_in_buf(int chan) {
    return ChannelFilters[chan].in_audio_buffer;
}

//TSF_STEREO_UNWEAVED
void synth_unweaved_filter_router(int chan, float* unweaved_audio, int samples)
{
    float *left = unweaved_audio;
    float *right = &left[samples];

    synth_filter_router(chan, left, right, samples);
}

void synth_interleaved_filter_router(int chan, float* interleaved_audio, int samples)
{
    float left[0xFFFF];
    float right[0xFFFF];
    int i;

    for(i = 0; i < samples/2; i++) {
        left[i] = interleaved_audio[2 *i];
        right[i] = interleaved_audio[2 * i+1];
    }

    // route to ladspa effects filter(s)
    synth_filter_router(chan, left, right, samples/2);
    // ^^^^^^^ gcsynth_filter routines

     // Reinterleave: output_buffer -> audio_buffer
     for (i = 0; i < samples/2; i++) {
        interleaved_audio[2 * i] = left[i]; // Left
        interleaved_audio[2 * i + 1] = right[i]; // Right
    }
    
}



int  gcsynth_channel_filter_is_enabled(int chan)
{
    int ret = 0;
    struct gcsynth_channel *c = lock_channel(chan);

    if (c) {
        ret = c->at_least_one_filter_enabled;
        unlock_channel(chan);
    }

    return ret;
}



//////////////////////////////////////////////////////////////////////




// --- static functions

static struct gcsynth_channel* lock_channel(int chan)
{
    struct gcsynth_channel* c = NULL;
    
    if ((chan >= 0) && (chan < NUM_CHANNELS)) { 
        c = &ChannelFilters[chan];

        if (c->initialized == 0) {
            g_mutex_init(&c->mutex);
            c->initialized = 1;
        }
        g_mutex_lock(&c->mutex);    
    }

    return c;
}

static void unlock_channel(int channel)
{
    if ((channel >= 0) && (channel < NUM_CHANNELS)) { 
        struct gcsynth_channel* c = &ChannelFilters[channel];
        g_mutex_unlock(&c->mutex); 
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
            printf("gcsynth: removing filter %s\n", f->desc->Label);

            gcsynth_filter_destroy(f);
            // unlink from double linked list.
            c->filter_chain = g_list_delete_link(c->filter_chain, iter);
        }
        else if (strcmp(f->desc->Label,plugin_label_or_all) == 0) {
            printf("gcsynth: removing filter %s\n", f->desc->Label);

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
        /*
        sprintf(errmsg,"gcsynth_channel_add_filter duplicate plugin name %s not allowed!", plugin_label);
        gcsynth_raise_exception(errmsg);
        return -1;
        */
       printf("Filter %s already added to filter chain, nothing to do\n", plugin_label);
       return 0;
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

    printf("gcsynth: adding filter %s, enabled = %d\n", f->desc->Label, f->enabled);

    return 0;
}

static int _gcsynth_channel_set_control_by_index(int channel,
    char* plugin_label, int control_num, float value)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel
    struct gcsynth_filter* f = find_by_name(c,plugin_label);

    return gcsynth_filter_setbyindex(f, control_num, value);
}

static int _gcsynth_channel_set_control_by_name(int channel,
    char* plugin_label, char* control_name, float value)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; // gcsynth.c validated channel
    struct gcsynth_filter* f = find_by_name(c,plugin_label);
    int i;
    int ret = FILTER_CONTROL_NO_FOUND;

    if (f) {
        ret = gcsynth_filter_setbyname(f, control_name, value);
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
 
static void set_channel_state(int channel, char* plugin_label, int enabled)
{
    struct gcsynth_channel* c = &ChannelFilters[channel]; 
    struct gcsynth_filter* f = find_by_name(c, plugin_label);
    GList* iter;

    if (f) {
        if (enabled) {
            gcsynth_filter_enable(f);
        } else {
            gcsynth_filter_disable(f);
        }
    }  

    c->at_least_one_filter_enabled = 0;
    for(iter = g_list_first(c->filter_chain);
            (iter != NULL) && (c->at_least_one_filter_enabled == 0);
            iter = iter->next
    ) {
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
        if (f->enabled) {
            c->at_least_one_filter_enabled = 1;
        }
    }  
}

/*
static GMutex StateMutex;
static int    StateMutexInitialized;
static struct gcsynth_active_state GcsynthState;
*/
struct gcsynth_active_state gcsynth_get_active_state()
{
    struct gcsynth_active_state state;

    if (StateMutexInitialized == 0) {
        g_mutex_init(&StateMutex);
        StateMutexInitialized = 1;
    }

    g_mutex_lock(&StateMutex);
    state = GcsynthState;
    g_mutex_unlock(&StateMutex); 

    return state;
}

void gcsynth_update_state_when_started()
{
    if (StateMutexInitialized == 0) {
        g_mutex_init(&StateMutex);
        StateMutexInitialized = 1;
    }
    g_mutex_lock(&StateMutex);
    GcsynthState.instance_id = GcsynthIdCount++;
    GcsynthState.running = 1;
    g_mutex_unlock(&StateMutex);
}

void gcsynth_update_state_when_stopped()
{
    if (StateMutexInitialized == 0) {
        g_mutex_init(&StateMutex);
        StateMutexInitialized = 1;
    }
    g_mutex_lock(&StateMutex);
    GcsynthState.running = 0;
    g_mutex_unlock(&StateMutex);
}
