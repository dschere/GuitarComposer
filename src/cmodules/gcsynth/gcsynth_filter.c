#include <stdlib.h>
#include <dlfcn.h>
#include <errno.h>
#include <string.h>
#include <math.h>

#include "gcsynth.h"
#include "gcsynth_filter.h"


static int ladspa_setup(struct gcsynth_filter* gc_filter, const char* path, char* label);
static void ladspa_deallocate(struct gcsynth_filter* gc_filter);


struct gcsynth_filter* gcsynth_filter_new_ladspa(const char* pathname, char* label)
{
    struct gcsynth_filter* gc_filter = (struct gcsynth_filter*)
        calloc(1, sizeof(struct gcsynth_filter));

    if (gc_filter != NULL) {
        if (ladspa_setup(gc_filter,pathname, label) == -1) {
            // exception already set, now clear memory/resources
            gcsynth_filter_destroy(gc_filter);
            return NULL;
        }
    } else {
        gcsynth_raise_exception("gcsynth_filter_new_ladspa: calloc failed.");
    }

    gc_filter->frame_count = 0;
    return gc_filter;    
}

// free all resources, the memory itself is freed so 'gc_filter' is
// no longer usable after this call. 
void gcsynth_filter_destroy(struct gcsynth_filter* gc_filter)
{
    if (gc_filter != NULL) {
        ladspa_deallocate(gc_filter);
    }
}

// sets the value of a control
int gcsynth_filter_setbyname(struct gcsynth_filter* gc_filter, char* name, LADSPA_Data value)
{
    return 0;
}

int gcsynth_filter_setbyindex(struct gcsynth_filter* gc_filter, int, LADSPA_Data value)
{
    return 0;
}

// sends FLUID_BUFSIZE size to the filter and copies FLUID_BUFSIZE out from the
// filter 
int gcsynth_filter_run(struct gcsynth_filter* gc_filter, LADSPA_Data* in, LADSPA_Data* out)
{
    return 0;
}


void gcsynth_enable(struct gcsynth_filter* gc_filter)
{
    gc_filter->enabled = 1;
}

void gcsynth_disable(struct gcsynth_filter* gc_filter)
{
    gc_filter->enabled = 0;
}

int  gcsynth_isEnabled(struct gcsynth_filter* gc_filter)
{
    return gc_filter->enabled;
}


static void ladspa_deallocate(struct gcsynth_filter* gc_filter)
{
    if (gc_filter->dl_handle) {
        dlclose(gc_filter->dl_handle);
        gc_filter->dl_handle = NULL;
    }
}


static void setup_ctl_value(struct gcsynth_filter* gc_filter, 
    int ctl, struct gcsynth_filter_control* control, int pd)
{
    const LADSPA_PortRangeHint *h = &gc_filter->desc->PortRangeHints[ctl];
    const LADSPA_Data lower = (h) ? h->LowerBound: 0;
    const LADSPA_Data upper = (h) ? h->UpperBound: 1000000.0;

    control->name = gc_filter->desc->PortNames[ctl];
    control->isOutput = 0;
    control->has_default = 1;
    
    control->lower = lower;
    control->upper = upper;

    control->is_bounded_above = LADSPA_IS_HINT_BOUNDED_ABOVE(h->HintDescriptor);
    control->is_bounded_below = LADSPA_IS_HINT_BOUNDED_BELOW(h->HintDescriptor);
    control->is_toggled = LADSPA_IS_HINT_TOGGLED(h->HintDescriptor);
    control->is_logarithmic = LADSPA_IS_HINT_LOGARITHMIC(h->HintDescriptor);
    control->is_integer = LADSPA_IS_HINT_INTEGER(h->HintDescriptor);

    if (LADSPA_IS_PORT_OUTPUT(pd)) {
        control->value = 0;
        control->isOutput = 1;
        control->has_default = 0;
    // otherwise it an input control port  
    } else if (LADSPA_IS_HINT_HAS_DEFAULT(h->HintDescriptor)) {
        control->has_default = 0;      
    } else if (LADSPA_IS_HINT_DEFAULT_MINIMUM(h->HintDescriptor)) {
        control->value = lower;
    } else if (LADSPA_IS_HINT_DEFAULT_MAXIMUM(h->HintDescriptor)) {
        control->value = upper;
    } else if (LADSPA_IS_HINT_DEFAULT_0(h->HintDescriptor)) {
        control->value = 0.0;
    } else if (LADSPA_IS_HINT_DEFAULT_1(h->HintDescriptor)) {
        control->value = 1.0;
    } else if (LADSPA_IS_HINT_DEFAULT_100(h->HintDescriptor)) {
        control->value = 100.0;
    } else if (LADSPA_IS_HINT_DEFAULT_440(h->HintDescriptor)) {
        control->value = 440.0;
    } else if (LADSPA_IS_HINT_DEFAULT_LOW(h->HintDescriptor)) {
        if (LADSPA_IS_HINT_LOGARITHMIC(h->HintDescriptor))
            control->value = exp(log(lower) * 0.75 + log(upper) * 0.25);
        else
            control->value = lower * 0.75 + upper * 0.25;
    } else if (LADSPA_IS_HINT_DEFAULT_MIDDLE(h->HintDescriptor)) {
        if (LADSPA_IS_HINT_LOGARITHMIC(h->HintDescriptor))
            control->value = exp(log(lower) * 0.5 + log(upper) * 0.5);
        else
            control->value = lower * 0.5 + upper * 0.5;
    } else if (LADSPA_IS_HINT_DEFAULT_HIGH(h->HintDescriptor)) {
        if (LADSPA_IS_HINT_LOGARITHMIC(h->HintDescriptor))
            control->value = exp(log(lower) * 0.25 + log(upper) * 0.75);
        else
            control->value = lower * 0.25 + upper * 0.75;
    }

    if (control->has_default) {
        control->default_value = control->value;
    }

}

static int ladspa_setup(struct gcsynth_filter* gc_filter, const char* path, char* label)
{
    char errmsg[256];
    long unsigned int i;
    int found = 0;

    gc_filter->dl_handle = NULL;

    // open the library with a local namespace so multipel opens of
    // the same library will use different internal variables.
    if ((gc_filter->dl_handle = dlopen(path, RTLD_LOCAL|RTLD_NOW)) == NULL) {
        sprintf(errmsg,"ladspa_setup dlopen failed %s", dlerror());
        gcsynth_raise_exception(errmsg);
        return -1;
    }

    if ((gc_filter->descriptor_fn = 
      dlsym(gc_filter->dl_handle, "ladspa_descriptor")) == NULL) {
        gcsynth_raise_exception("dlsym failed to load ladspa_descriptor()");
        ladspa_deallocate(gc_filter);
        return -1;
    }

    // search for plugin that matches label, some ladspa plugins have multiple
    // plugins within the same shared library.
    for(i = 0; found == 0; i++)
     {
        if ((gc_filter->desc = gc_filter->descriptor_fn(i)) == NULL) {
            sprintf(errmsg,"No match for plugin name %s in %s", label, path);
            gcsynth_raise_exception(errmsg);
            ladspa_deallocate(gc_filter);
            return -1;
        }
        found = strcmp(gc_filter->desc->Label,label) == 0;
    }

    // instanciate plugin, then associate buffers.
    gc_filter->plugin_instance = gc_filter->desc->instantiate(gc_filter->desc, SAMPLE_RATE);
    if (!gc_filter->plugin_instance) {
        gcsynth_raise_exception("gc_filter->desc->instantiate() failed!");
        ladspa_deallocate(gc_filter);
        return -1;
    }

    // cycle through ports and assign buffers, some plunins are stereo others
    // are mono, in the case of the latter then only the left channel is used
    gc_filter->num_controls = 0;
    gc_filter->in_buf_count = 0;
    gc_filter->out_buf_count = 0;
    
    for(i = 0; i < gc_filter->desc->PortCount; i++) {
        int pd = gc_filter->desc->PortDescriptors[i];

        // setup input port(s) 
        if (LADSPA_IS_PORT_AUDIO(pd) && 
            LADSPA_IS_PORT_INPUT(pd) &&
            gc_filter->in_buf_count < NUM_IO_PORTMAPS) {
            
            gc_filter->desc->connect_port(
                gc_filter->plugin_instance,
                i,
                gc_filter->in_data_buffer[gc_filter->in_buf_count]
            );
            gc_filter->in_buf_count++;
        }
        // setup output port(s)
        else 
        if (LADSPA_IS_PORT_AUDIO(pd) && 
            LADSPA_IS_PORT_OUTPUT(pd) &&
            gc_filter->out_buf_count < NUM_IO_PORTMAPS) {

            gc_filter->desc->connect_port(
                gc_filter->plugin_instance,
                i,
                gc_filter->out_data_buffer[gc_filter->out_buf_count]
            );
            gc_filter->out_buf_count++;
        }   
        // setup control ports
        else if (LADSPA_IS_PORT_CONTROL(pd) && 
        gc_filter->num_controls < MAX_LADSPA_CONTROLS) {

            // setup structure, ranges, and a default value.
            setup_ctl_value(gc_filter, 
               i, &gc_filter->controls[gc_filter->num_controls], pd);

            gc_filter->desc->connect_port(
                gc_filter->plugin_instance,
                i,
                &gc_filter->controls[gc_filter->num_controls].value
            );

            // increment the number of controls
            gc_filter->num_controls++;
        }
    }

    // the ports are setup and the plugin instanciated.

    return 0;
}