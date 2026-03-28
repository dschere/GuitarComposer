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
#include "freqdomain.h"

#include <stdio.h>




void fg_set_band_attribute(struct fgraph_node *node, int att_id, int ival, float fval, char* sval)
{
    struct fgraph_bandpass* bandpass = NULL;
    struct fgraph_lowpass*  lowpass = NULL;
    struct fgraph_highpass* highpass = NULL;

    switch(node->base.type) {
        case FG_NODE_TYPE_BANDPASS:
            bandpass = (struct fgraph_bandpass*) node;
            switch(att_id) {
                case AID_BAND_PASS_LOW_FREQ:
                    bandpass->freq_low = fval;
                    break;
                case AID_BAND_PASS_HIGH_FREQ:
                    bandpass->freq_high = fval;
                    break;
                case AID_ENABLE_FALLBACK_METHOD:
                    node->using_fallback_method_for_freqdomain = 1;
                    midi_filter_decrement(); // reduce counter since we are not using precalulated buffers
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
                    node->using_fallback_method_for_freqdomain = 0;
                    midi_filter_increment(); // use precalculated buffers
                    gcsynth_filter_disable(bandpass->fallback_lowpass);
                    gcsynth_filter_disable(bandpass->fallback_highpass);

                    gcsynth_filter_destroy(bandpass->fallback_lowpass);
                    gcsynth_filter_destroy(bandpass->fallback_highpass);
                    break;    
            } 
            break;
        case  FG_NODE_TYPE_LOWPASS:
            lowpass = (struct fgraph_lowpass*) node;
            switch(att_id) {
                case AID_LOW_PASS_FREQ:
                    lowpass->freq = fval;
                    break;
                case AID_ENABLE_FALLBACK_METHOD:
                    node->using_fallback_method_for_freqdomain = 1;
                    lowpass->fallback_lowpass = gcsynth_filter_new_ladspa(
                        FALLBACK_LOWPASS_FILTER_DEF_PATH, 
                        FALLBACK_LOWPASS_FILTER_DEF_NAME);
                    gcsynth_filter_enable(bandpass->fallback_lowpass);
                    break;
                case AID_DISABLE_FALLBACK_METHOD:
                    node->using_fallback_method_for_freqdomain = 0;
                    gcsynth_filter_disable(lowpass->fallback_lowpass);
                    gcsynth_filter_destroy(lowpass->fallback_lowpass);
                    break;    
            }
            break;
        case  FG_NODE_TYPE_HIGHPASS:
            highpass = (struct fgraph_highpass*) node;
            switch(att_id) {
                case AID_HIGH_PASS_FREQ:
                    highpass->freq = fval;
                    break;
                case AID_ENABLE_FALLBACK_METHOD:
                    node->using_fallback_method_for_freqdomain = 1;
                    highpass->fallback_highpass = gcsynth_filter_new_ladspa(
                        FALLBACK_HIGHASS_FILTER_DEF_PATH, 
                        FALLBACK_HIGHPASS_FILTER_NAME);
                    gcsynth_filter_enable(highpass->fallback_highpass);
                    break;
                case AID_DISABLE_FALLBACK_METHOD:
                    node->using_fallback_method_for_freqdomain = 0;
                    gcsynth_filter_disable(highpass->fallback_highpass);
                    gcsynth_filter_destroy(highpass->fallback_highpass);
                    break;                    
            }
            break;
        default: {
            char error_msg[256];

            sprintf(error_msg,"Programmatic error unknown type %d\n", node->base.type);
            gcsynth_raise_exception(error_msg);
            }
            return;
    }


}


int lowpass_run(struct fgraph_node* node, float* left, float* right)
{
    struct fgraph_lowpass* lp = (struct fgraph_lowpass*) node; 
    int r = 0;

    if (node->using_fallback_method_for_freqdomain == 1) {

        // according to plugin documentation the max freq value is
        // 0.45 * sample rate -> 6498.0
        int max_freq = 6498.0;
        char errmsg[256];

        if (lp->freq > max_freq) {
            sprintf(errmsg,"lowpass_run freq %f out of range\n", lp->freq);
            gcsynth_raise_exception(errmsg);
            return -1;
        } 

        // first low pass filter
        if ((r = gcsynth_filter_setbyindex(lp->fallback_lowpass, 0, lp->freq)) != 0 ) {return r;}
        if ((r = gcsynth_filter_run_sterio(lp->fallback_lowpass, left, right, AUDIO_SAMPLES)) != 0) {return r;}
    } else {
        fg_lowpass_filter(node->channel, lp->freq, left, right);
    }

    return r;
}


int highpass_run(struct fgraph_node* node, float* left, float* right)
{
    struct fgraph_highpass* hp = (struct fgraph_highpass*) node; 
    int r;

    if (node->using_fallback_method_for_freqdomain == 1) {

        // according to plugin documentation the max freq value is
        // 0.45 * sample rate -> 6498.0
        int max_freq = 6498.0;
        char errmsg[256];

        if (hp->freq > max_freq) {
            sprintf(errmsg,"highpass_run freq %f out of range\n", hp->freq);
            gcsynth_raise_exception(errmsg);
            return -1;
        } 

        // first low pass filter
        if ((r = gcsynth_filter_setbyindex(hp->fallback_highpass, 0, hp->freq)) != 0 ) {return r;}
        if ((r = gcsynth_filter_run_sterio(hp->fallback_highpass, left, right, AUDIO_SAMPLES)) != 0) {return r;}
    } else {
        r = fg_highpass_filter(node->channel, hp->freq, left, right);
    }

    return r;

}


int bandpass_run(struct fgraph_node* node, float* left, float* right)
{
    struct fgraph_bandpass* bp = (struct fgraph_bandpass*) node; 
    int r;

    if (node->using_fallback_method_for_freqdomain == 1) {
        // according to plugin documentation the max freq value is
        // 0.45 * sample rate -> 6498.0
        int max_freq = 6498.0;
        char errmsg[256];

        if (bp->freq_low > max_freq) {
            sprintf(errmsg,"bandpass_run freq_low %f out of range\n", bp->freq_low);
            gcsynth_raise_exception(errmsg);
            return -1;
        } 

        if (bp->freq_high > max_freq) {
            sprintf(errmsg,"bandpass_run freq_high %f out of range\n", bp->freq_high);
            gcsynth_raise_exception(errmsg);
            return -1;
        } 

        /* must simulate band pass with two filters low and high*/
        // first low pass filter
        if ((r = gcsynth_filter_setbyindex(bp->fallback_lowpass, 0, bp->freq_low)) != 0 ) {return r;}
        if ((r = gcsynth_filter_run_sterio(bp->fallback_lowpass, left, right, AUDIO_SAMPLES)) != 0) {return r;}
        // then high pass filter
        if ((r = gcsynth_filter_setbyindex(bp->fallback_highpass, 0, bp->freq_high)) != 0 ) {return r;}
        if ((r = gcsynth_filter_run_sterio(bp->fallback_highpass, left, right, AUDIO_SAMPLES)) != 0) {return r;}
    } else {
        r = fg_bandpass_filter(node->channel, bp->freq_low, bp->freq_high, left, right);
    }

    return r;
}


