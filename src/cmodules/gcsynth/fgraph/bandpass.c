/**
 * This module abstracts two differnt kind of filter implements for
 * band pass, low pass and high pass filters.
 * 
 * The first approach takes advantage of the fact that for synth
 * generated audio we know the frequencies being generated. Furthermore
 * we can store the frequencies and harmonics into buffers. Creating
 * a this frequency based filter is simply mixining defined bufferes
 * without any signal processing.
 * 
 * For live audio we need to use signal analysis for a traditional 
 * band pass filter using a LADSPA filter.
 * 
 */
#include "bandpass.h"
#include "fgraph.h"

#include <stdio.h>




void fg_set_band_attribute(struct fgraph_node *node, int att_id, int ival, float fval, char* sval)
{
    struct fgraph_bandpass* bandpass = NULL;
    struct fgraph_lowpass*  lowpass = NULL;
    struct fgraph_highpass* highpass = NULL;

    switch(node->base.type) {
        case FG_BAND_PASS:
            bandpass = (struct fgraph_bandpass*) node;
            switch(att_id) {
                case AID_BAND_PASS_LOW_FREQ:
                    bandpass->freq_low = fval;
                    break;
                case AID_BAND_PASS_HIGH_FREQ:
                    bandpass->freq_high = fval;
                    break;
                case AID_ENABLE_FALLBACK_METHOD:
                    bandpass->node.using_fallback_method_for_freqdomain = 1;
                    bandpass->fallback_lowpass = gcsynth_filter_new_ladspa(
                        FALLBACK_LOWPASS_FILTER_DEF_PATH, 
                        FALLBACK_LOWPASS_FILTER_DEF_NAME);
                    bandpass->fallback_highpass = gcsynth_filter_new_ladspa(
                        FALLBACK_HIGHASS_FILTER_DEF_PATH, 
                        FALLBACK_HIGHPASS_FILTER_NAME);
                    gcsynth_filter_enable(bandpass->fallback_lowpass);
                    gcsynth_filter_enable(bandpass->fallback_highpass);
                    break;
                case AID_DISABLE_FALLBACK_METHOD:
                    bandpass->node.using_fallback_method_for_freqdomain = 1;
                    gcsynth_filter_disable(bandpass->fallback_lowpass);
                    gcsynth_filter_disable(bandpass->fallback_highpass);

                    gcsynth_filter_destroy(bandpass->fallback_lowpass);
                    gcsynth_filter_destroy(bandpass->fallback_highpass);
                    break;    
            } 
            break;
        case FG_LOW_PASS:
            lowpass = (struct fgraph_lowpass*) node;
            break;
        case FG_HIGH_PASS:
            highpass = (struct fgraph_highpass*) node;
            break;
        default: {
            char error_msg[256];

            sprintf(error_msg,"Programmatic error unknown type %d\n", node->base.type);
            gcsynth_raise_exception(error_msg);
            }
            return;
    }


}


void lowpass_run(struct fgraph_lowpass* node, float* left, float* right)
{
    
}


void highpass_run(struct fgraph_highpass* node, float* left, float* right)
{
    
}


void bandpass_run(struct fgraph_bandpass* node, float* left, float* right)
{
    
}


