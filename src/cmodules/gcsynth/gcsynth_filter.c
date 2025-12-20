#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <errno.h>
#include <string.h>
#include <math.h>

#include "gcsynth.h"
#include "gcsynth_filter.h"

#define MONO_FILTER   1
#define STEREO_FILTER 2

static int ladspa_setup(struct gcsynth_filter* gc_filter, const char* path, char* label);
static void ladspa_deallocate(struct gcsynth_filter* gc_filter);
static LADSPA_Data get_default_value(
    struct gcsynth_filter* gc_filter, unsigned long int lPortIndex,
    int* has_default);
static void gcsynth_filter_report(struct gcsynth_filter* gc_filter);


struct gcsynth_filter* gcsynth_filter_new_ladspa(const char* pathname, char* label)
{
    struct gcsynth_filter* gc_filter = (struct gcsynth_filter*)
        calloc(1, sizeof(struct gcsynth_filter));

    if (gc_filter != NULL) {
        if (ladspa_setup(gc_filter,pathname, label) == -1) {
            // exception already set, now clear memory/resources which 
            // may have been allocated.
            gcsynth_filter_destroy(gc_filter);
            gc_filter = NULL;
        } else {
            gc_filter->frame_count = 0;
        } 
    } else {
        gcsynth_raise_exception("gcsynth_filter_new_ladspa: calloc failed.");
    }

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

// // sets the value of a control
// int gcsynth_filter_setbyname(struct gcsynth_filter* gc_filter, char* name, LADSPA_Data value)
// {
//     return 0;
// }

// int gcsynth_filter_setbyindex(struct gcsynth_filter* gc_filter, int, LADSPA_Data value)
// {
//     return 0;
// }


static
int gcsynth_interleaved_filter_run(struct gcsynth_filter* gc_filter, LADSPA_Data* fc_buffer, int len) 
{
    int i,  j;

    for(i =0, j=0; i < len; i += 2, j++) {
        gc_filter->in_data_buffer[0][j] = fc_buffer[i];
        gc_filter->in_data_buffer[1][j] = fc_buffer[i+1];
    }

    for(i = 0; i < (int) gc_filter->desc->PortCount; i++) {
        gc_filter->desc->connect_port(
            gc_filter->plugin_instance,
            i,
            gc_filter->port_map[i]
        );
    }
    
    // run the filter and populate the output buffer
    printf("gcsynth_interleaved_filter_run run()\n");
    gc_filter->desc->run(gc_filter->plugin_instance, len/2);

    for(i =0, j=0; i < len; i += 2, j++) {
        fc_buffer[i] = gc_filter->out_data_buffer[0][j];
        fc_buffer[i+1] = gc_filter->out_data_buffer[1][j];
    } 

    return 0;
}

// #include "gccmacro.h"
// static void clamp(float* right, float* left, int samples)
// {
//     int i;
//     for(i = 0; i < samples; i++) {
//         right[i] = PA_CLAMP_UNLIKELY(right[i], -1.0f, 1.0f);
//         left[i] = PA_CLAMP_UNLIKELY(left[i], -1.0f, 1.0f);
//     }
// }

#define MICRO_EPSILON 1e-4    // Define the threshold 

static inline void truncate_coefficient(float *value) {
    if (fabsf(*value) < MICRO_EPSILON) {
        *value = 0.0f;
    }
}


int gcsynth_filter_run_sterio(
    struct gcsynth_filter* gc_filter, float* left, float* right, int samples)
{
    int i=0;

    if (gc_filter->enabled) {
        //clamp(right, left, samples);

        //for(i = 0; i < samples; i++) {
        //    truncate_coefficient(&left[i]);
        //    truncate_coefficient(&right[i]);
        //}

        switch(gc_filter->in_buf_count) {
            case STEREO_FILTER:
                if (gc_filter->in_place_supported) {
                    gc_filter->desc->connect_port(
                        gc_filter->plugin_instance,
                        gc_filter->left_in_idx,
                        left
                    );
            
                    gc_filter->desc->connect_port(
                        gc_filter->plugin_instance,
                        gc_filter->right_in_idx,
                        right
                    );

                    gc_filter->desc->connect_port(
                        gc_filter->plugin_instance,
                        gc_filter->left_out_idx,
                        left
                    );
            
                    gc_filter->desc->connect_port(
                        gc_filter->plugin_instance,
                        gc_filter->right_out_idx,
                        right
                    );
                } else {
                    memcpy(gc_filter->in_data_buffer[0],left,samples * sizeof(float));
                    memcpy(gc_filter->in_data_buffer[1],right,samples* sizeof(float));
                }
                break;
            case MONO_FILTER:
                // stereo to mono
                if (gc_filter->in_place_supported) {
                    // the plugin was configured to use the same buffer 
                    // for input and output.
                    for(i = 0; i < samples; i++) {
                        gc_filter->out_data_buffer[0][i] = (left[i] + right[i]) * 0.5f;
                     } 
                } else {
                    for(i = 0; i < samples; i++) {
                       gc_filter->in_data_buffer[0][i] = (left[i] + right[i]) * 0.5f;
                    }
                }
                break;
        }

        // execute ladspa plugin to populate audio buffer
        gc_filter->desc->run(gc_filter->plugin_instance, samples);

        switch(gc_filter->out_buf_count) {
            case STEREO_FILTER:
                break;
            case MONO_FILTER:
                // mono to stereo
                for(i = 0; i < samples; i++) {
                    left[i] = (float) gc_filter->out_data_buffer[0][i];
                    right[i] = left[i];
                }
                break;    
        }

        //clamp(right, left, samples);
    }    
    return 0;
}


// sends FLUID_BUFSIZE size to the filter and copies FLUID_BUFSIZE out from the
// filter 
int gcsynth_filter_run(struct gcsynth_filter* gc_filter, LADSPA_Data* fc_buffer, int len)
{
    unsigned long int i;
//    int io_count;

    if (gc_filter->enabled) {
        if (gc_filter->in_buf_count == 2 && gc_filter->out_buf_count == 2) {
            return gcsynth_interleaved_filter_run(gc_filter, fc_buffer, len);
        }

        /*
            Ladspa filters can be either stereo or mono. The voice_data_router gets called
            once for left and once for right so in the case of stereo we   
        */

        // for(io_count = 0; io_count < gc_filter->in_buf_count; io_count++ ) {
        //     memcpy(gc_filter->in_data_buffer[io_count], fc_buffer, len);            
        // }       

        // there are filters that just output (like wave generators)
        // so in that case in_buf_count is 0 
        if (gc_filter->in_buf_count > 0) {
            memcpy(                           //  either modulo 1 or 2
                gc_filter->in_data_buffer[0],
                fc_buffer,
                len
            );
        }

        // connect all ports
        for(i = 0; i < gc_filter->desc->PortCount; i++) {
            gc_filter->desc->connect_port(
                gc_filter->plugin_instance,
                i,
                gc_filter->port_map[i]
            );
        }
        
        // run the filter and populate the output buffer
        printf("gcsynth_filter_run run()\n"); 
        gc_filter->desc->run(gc_filter->plugin_instance, len);

        // for(i = 0; i < len; i++) {
        //     if (gc_filter->out_buf_count == 1) {
        //         fc_buffer[i] = gc_filter->out_data_buffer[0][i];
        //     } else if (gc_filter->out_buf_count == 2) {
        //         fc_buffer[i] = (
        //             (gc_filter->out_data_buffer[0][i] + gc_filter->out_data_buffer[1][i])
        //         );
        //     }
        // }
        
        // output to fc_buffer from filter output
        if (gc_filter->out_buf_count > 0) {
            memcpy(
                fc_buffer,
                gc_filter->out_data_buffer[0],
                len
            );
        }

    } else {
        //printf("disabled\n");
    }
    
    gc_filter->frame_count++;

    return 0;
}



void gcsynth_filter_enable(struct gcsynth_filter* gc_filter)
{
    if (gc_filter->enabled == 0) {
        gc_filter->enabled = 1;
        gcsynth_filter_report(gc_filter);
    }
 
    if (gc_filter->desc->activate) {
        gc_filter->desc->activate(gc_filter->plugin_instance);
    }   
}

void gcsynth_filter_disable(struct gcsynth_filter* gc_filter)
{
    if (gc_filter->enabled == 1) {
        gc_filter->enabled = 0;
        printf("gcsynth: %s deactivated\n", gc_filter->desc->Label);
    }

    if (gc_filter->desc->deactivate)
    {
        gc_filter->desc->deactivate(gc_filter->plugin_instance);
    }
}

int  gcsynth_filter_isEnabled(struct gcsynth_filter* gc_filter)
{
    return gc_filter->enabled;
}


static void ladspa_deallocate(struct gcsynth_filter* gc_filter)
{
    if (gc_filter->gmodule != NULL) {
        if (gc_filter->plugin_instance && gc_filter->desc) {
            gcsynth_filter_disable(gc_filter);

            if(gc_filter->desc->cleanup != NULL)
            {
                gc_filter->desc->cleanup(gc_filter->plugin_instance);
            }
        }

        g_module_close(gc_filter->gmodule);
        memset(gc_filter, 0, sizeof(struct gcsynth_filter));
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

    control->default_value = 
       get_default_value(gc_filter, (unsigned long int) ctl,
            &control->has_default);

    if (LADSPA_IS_PORT_OUTPUT(pd)) {
        control->value = 0;
        control->isOutput = 1;
        control->has_default = 0;
    }

    if (control->has_default) {
        control->value = control->default_value;
    }

    printf("Updated %s, set control %s to %f\n",
        gc_filter->desc->Label, control->name, control->value);

}


static int ladspa_setup(struct gcsynth_filter* gc_filter, const char* path, char* label)
{
    char errmsg[256];
    long unsigned int i;
    int found = 0;

    memset(gc_filter, 0, sizeof(struct gcsynth_filter));

    gc_filter->gmodule = g_module_open(path, G_MODULE_BIND_LOCAL);
    if (gc_filter->gmodule == NULL) {
        sprintf(errmsg,"gcsynth: ladspa_setup dlopen failed %s", dlerror());
        gcsynth_raise_exception(errmsg);
        return -1;
    }

    if (!g_module_symbol(gc_filter->gmodule, "ladspa_descriptor", 
        (gpointer) &gc_filter->descriptor_fn)) {
        gcsynth_raise_exception("dlsym failed to load ladspa_descriptor()");
        ladspa_deallocate(gc_filter);
        return -1;
    }

    // search for plugin that matches label, some ladspa plugins have multiple
    // plugins within the same shared library.
    for(i = 0; found == 0; i++)
     {
        if ((gc_filter->desc = gc_filter->descriptor_fn(i)) == NULL) {
            sprintf(errmsg,"gcsynth: No match for plugin name %s in %s", label, path);
            gcsynth_raise_exception(errmsg);
            ladspa_deallocate(gc_filter);
            return -1;
        }
        found = strcmp(gc_filter->desc->Label,label) == 0;
    }

    // instanciate plugin, then associate buffers.
    // see if this works
    gc_filter->plugin_instance = gc_filter->desc->instantiate(gc_filter->desc, SAMPLE_RATE);
    if (gc_filter->plugin_instance == NULL) {
        gcsynth_raise_exception("gc_filter->desc->instantiate() failed!");
        ladspa_deallocate(gc_filter);
        return -1;
    }

    // cycle through ports and assign buffers, some plunins are stereo others
    // are mono, in the case of the latter then only the left channel is used
    gc_filter->num_controls = 0;
    gc_filter->in_buf_count = 0;
    gc_filter->out_buf_count = 0;

    if (LADSPA_IS_INPLACE_BROKEN(gc_filter->desc->Properties)) {
        gc_filter->in_place_supported = 0;
    } else {
        gc_filter->in_place_supported = 1;
    }
    
    for(i = 0; i < gc_filter->desc->PortCount; i++) {
        int pd = gc_filter->desc->PortDescriptors[i];

        // setup input port(s) 
        if (LADSPA_IS_PORT_AUDIO(pd) && 
            LADSPA_IS_PORT_INPUT(pd) &&
            gc_filter->in_buf_count < NUM_IO_PORTMAPS) {

            gc_filter->port_map[i] = gc_filter->in_data_buffer[gc_filter->in_buf_count];

            // printf("gcsynth: input port %lu (%s) to input host  buffer %d\n",
            //      i, gc_filter->desc->PortNames[i], 
            //      gc_filter->in_buf_count
            // );

            if (gc_filter->in_buf_count) {
                gc_filter->left_in_idx = (int) i;
            } else {
                gc_filter->right_in_idx = (int) i;
            }

            gc_filter->in_buf_count++;
        }
        // setup output port(s)
        else 
        if (LADSPA_IS_PORT_AUDIO(pd) && 
            LADSPA_IS_PORT_OUTPUT(pd) &&
            gc_filter->out_buf_count < NUM_IO_PORTMAPS) {

            gc_filter->port_map[i] = gc_filter->out_data_buffer[gc_filter->out_buf_count];
            // printf("gcsynth: output port %lu (%s) to output host buffer %d\n",
            //      i, gc_filter->desc->PortNames[i], 
            //      gc_filter->out_buf_count
            // );
            if (gc_filter->out_buf_count) {
                gc_filter->left_out_idx = (int) i;
            } else {
                gc_filter->right_out_idx = (int) i;
            }

            gc_filter->out_buf_count++;
        }   
        // setup control ports
        else if (LADSPA_IS_PORT_CONTROL(pd) && 
            gc_filter->num_controls < MAX_LADSPA_CONTROLS) {

            // setup structure, ranges, and a default value.
            setup_ctl_value(gc_filter, 
               i, &gc_filter->controls[gc_filter->num_controls], pd);
            gc_filter->port_map[i] = &gc_filter->controls[gc_filter->num_controls].value;   

            // printf("gcsynth: control port %lu (%s) to control buffer, default %f\n",
            //      i, gc_filter->desc->PortNames[i], 
            //      gc_filter->controls[gc_filter->num_controls].value);

            // increment the number of controls
            gc_filter->num_controls++;
        }
    }


    // connect all ports, must be called before activate
    for(i = 0; i < gc_filter->desc->PortCount; i++) {
        gc_filter->desc->connect_port(
            gc_filter->plugin_instance,
            i,
            gc_filter->port_map[i]
        );
    }

    if (gc_filter->in_place_supported) {
        // reconnect ports to use the same buffer for 
        // input as output.
        gc_filter->desc->connect_port(
            gc_filter->plugin_instance,
            gc_filter->left_in_idx,
            gc_filter->port_map[gc_filter->left_out_idx]
        );

        gc_filter->desc->connect_port(
            gc_filter->plugin_instance,
            gc_filter->right_in_idx,
            gc_filter->port_map[gc_filter->right_out_idx]
        );

        printf("Inplace buffer configuartion");
    }


    // enable filter by default
    gcsynth_filter_enable(gc_filter);

    return 0;
}
// this code was lifted/refactored from analyseplugin utility
static LADSPA_Data get_default_value(
    struct gcsynth_filter* gc_filter, unsigned long int lPortIndex, int* has_default)
{
    LADSPA_Data fDefault = 0;
    const LADSPA_Descriptor * psDescriptor = gc_filter->desc;
    int iHintDescriptor = psDescriptor->PortRangeHints[lPortIndex].HintDescriptor;

    *has_default = 1;

    switch (iHintDescriptor & LADSPA_HINT_DEFAULT_MASK) {
	case LADSPA_HINT_DEFAULT_NONE:
      *has_default = 0;
	  break;
	case LADSPA_HINT_DEFAULT_MINIMUM:
	  fDefault = psDescriptor->PortRangeHints[lPortIndex].LowerBound;
	  break;
	case LADSPA_HINT_DEFAULT_LOW:
	  if (LADSPA_IS_HINT_LOGARITHMIC(iHintDescriptor)) {
	    fDefault 
	      = exp(log(psDescriptor->PortRangeHints[lPortIndex].LowerBound) 
		    * 0.75
		    + log(psDescriptor->PortRangeHints[lPortIndex].UpperBound) 
		    * 0.25);
	  }
	  else {
	    fDefault 
	      = (psDescriptor->PortRangeHints[lPortIndex].LowerBound
		 * 0.75
		 + psDescriptor->PortRangeHints[lPortIndex].UpperBound
		 * 0.25);
	  }
	  break;
	case LADSPA_HINT_DEFAULT_MIDDLE:
	  if (LADSPA_IS_HINT_LOGARITHMIC(iHintDescriptor)) {
	    fDefault 
	      = sqrt(psDescriptor->PortRangeHints[lPortIndex].LowerBound
		     * psDescriptor->PortRangeHints[lPortIndex].UpperBound);
	  }
	  else {
	    fDefault 
	      = 0.5 * (psDescriptor->PortRangeHints[lPortIndex].LowerBound
		       + psDescriptor->PortRangeHints[lPortIndex].UpperBound);
	  }
	  break;
	case LADSPA_HINT_DEFAULT_HIGH:
	  if (LADSPA_IS_HINT_LOGARITHMIC(iHintDescriptor)) {
	    fDefault 
	      = exp(log(psDescriptor->PortRangeHints[lPortIndex].LowerBound) 
		    * 0.25
		    + log(psDescriptor->PortRangeHints[lPortIndex].UpperBound) 
		    * 0.75);
	  }
	  else {
	    fDefault 
	      = (psDescriptor->PortRangeHints[lPortIndex].LowerBound
		 * 0.25
		 + psDescriptor->PortRangeHints[lPortIndex].UpperBound
		 * 0.75);
	  }
	  break;
	case LADSPA_HINT_DEFAULT_MAXIMUM:
	  fDefault = psDescriptor->PortRangeHints[lPortIndex].UpperBound;
	  break;
	case LADSPA_HINT_DEFAULT_0:
	  fDefault = 0.0;
	  break;
	case LADSPA_HINT_DEFAULT_1:
	  fDefault = 1.0;
	  break;
	case LADSPA_HINT_DEFAULT_100:
	  fDefault = 100.0;
	  break;
	case LADSPA_HINT_DEFAULT_440:
	  fDefault = 440.0;
	  break;
	}

// printf("gcsynth: %s set to %f has_default=%d, iHintDescriptor=0x%X lPortIndex=%lu\n", 
//     psDescriptor->PortNames[lPortIndex], fDefault, *has_default, iHintDescriptor, lPortIndex);

    return fDefault;
}

static void gcsynth_filter_report(struct gcsynth_filter* gc_filter)
{
    int i;

    printf("gcsynth_filter %s\n", gc_filter->desc->Label);
    printf("-------------------------------\n");
    printf("enabled %d\n", gc_filter->enabled);
    for (i = 0; i < gc_filter->num_controls; i++) {
        printf("    %24s = %f\n", 
            gc_filter->controls[i].name,
            gc_filter->controls[i].value);
    }
}
