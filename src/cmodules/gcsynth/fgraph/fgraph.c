#include "../gcsynth_filter_graph.h"
#include <string.h>


void fg_init(struct gcsynth_filter_graph* fg)
{
    memset(fg, 0, sizeof(struct gcsynth_filter_graph));
}


void fg_enable(struct gcsynth_filter_graph* fg, int enabled)
{
    fg->enabled = enabled;
}


void fg_proc_balance_gain(float balance, float gain, float* left, float* right)
{
    int i;
    float right_mul, left_mul;

    if ((balance != 0.0) || (gain != 0.0) ) {
        if (balance >= -1.0 && balance <= 1.0) {
            right_mul = (1-balance);
            left_mul = 2.0 - right_mul;
        }
        for( i = 0; i < AUDIO_SAMPLES; i++) {
            left[i] = (left[i] * left_mul) * (1+gain);
            right[i] = (right[i] * right_mul) * (1+gain);
        }
    }
}

/**
 * 1. copy left/right to input buffer 
 * 2. pre demux processing
 * 3. cycle through demux filter chains
 * 4. mix the output of all chains
 * 5. apply post mux processing
 */
void fg_run(struct gcsynth_filter_graph* fg, int channel, float* left, float* right)
{
    if (fg->enabled) {
        fg->out_left = left;
        fg->out_right = right;

        if (fg->demuxer.num_chains == 0) {
            // in this case there is no filter chain. Only the pre demux filters
            // and balance and gain being used. No need to waste time copying
            // data to buffers we can do everything in the left/right buffers
            // provided.
            pre_demux_proc(fg, left, right);
        } else {
            // 1. copy left/right to input buffer
            memcpy(fg->in_left, left, sizeof(fg->in_left));
            memcpy(fg->in_right, right, sizeof(fg->in_right));

            // 2. pre demux effects (such as a noise gate, compressor)
            pre_demux_proc(fg, fg->in_left, fg->in_right);

            // 3. apply audio effects to each filter chain 
            demux_proc(fg, channel);

            // 4. mux the output from all filter chains.
            muxer_proc(fg);
        }

        // apply balance and gain.
        fg_proc_balance_gain(fg->balance, fg->gain, left, right);
    }
}

int fg_create_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    const char* pathname, 
    char* label 
)
{
    int error = 0;
    struct gcsynth_filter* f = gcsynth_filter_new_ladspa(pathname, label);

    if (f == NULL) {
        error = -1;
    } else {
        if (chain_idx == -1) {
            fg->pre_demux_effects = g_list_append(fg->pre_demux_effects, f);
            fg->filter_enabled_count++;
        } else if ((chain_idx >= 0) && (chain_idx < MAX_FILTER_CHAINS)) {
            struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_idx];
            chain->effects = g_list_append(chain->effects, f);
            fg->filter_enabled_count++;
        }  else {
            error = -1;
            gcsynth_filter_destroy(f);
            gcsynth_raise_exception("filter chain index out of range!");
        }
    }

    return error;
}


// primitive that searches for a filter by label in a filter chain
// or pre demux filter. 
struct fg_find_filter_result fg_find_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    char* label
){
    struct fg_find_filter_result result; 
    
    memset(&result, 0, sizeof(struct fg_find_filter_result));
    if (chain_idx == -1) {
        GList* iter;
        for(iter = g_list_first(fg->pre_demux_effects);
            iter != NULL;
            iter = iter->next
        ) {
            struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data; 
            if (strcmp(f->desc->Label, label) == 0) {
                result.list = &fg->pre_demux_effects;
                result.iter = iter;
                result.filter = f;
                result.found = 1;
                break;
            }
        }
    } else if ((chain_idx >= 0) && (chain_idx < MAX_FILTER_CHAINS)){
        // this is the deletion of a specific audio filter within a chain.
        struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_idx];
        GList* iter;
        for(iter = g_list_first(chain->effects);
            iter != NULL;
            iter = iter->next
        ) {
            struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data; 
            if (strcmp(f->desc->Label, label) == 0) {
                result.list = &chain->effects;
                result.iter = iter;
                result.filter = f;
                result.found = 1;
            }
        }
    } 
    
    return result;
}



int fg_remove_filter(
    struct gcsynth_filter_graph* fg,
    int chain_idx, // -1 means this filter is applied pre-demux
    const char* label
) {
    struct fg_find_filter_result result =  
        fg_find_filter(fg,chain_idx,label);

    if (result.found == 1) {
        GList* list = *result.list;
        
        list = g_list_delete_link(list, result.iter);
        fg->filter_enabled_count--;
    }
    return result.found;
}