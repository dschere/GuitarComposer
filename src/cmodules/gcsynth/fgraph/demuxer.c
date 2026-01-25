#include "../gcsynth_filter_graph.h"
#include "../gcsynth_filter.h"

enum {
    PARAM_BY_NAME,
    PARAM_BY_INDEX
};

static int fg_demux_set_param(struct gcsynth_filter_graph* fg, int chain_idx,
    char* label, int ktype, char* name, int pidx, float value)
{
    int res = -1;
    struct fg_find_filter_result result =  
        fg_find_filter(fg,chain_idx,label);

    if (result.found == 1) {
        struct gcsynth_filter* f = result.filter;
        switch(ktype) {
            case PARAM_BY_NAME:
                res = gcsynth_filter_setbyname(f, name, value);
                break; 
            case PARAM_BY_INDEX:
                res = gcsynth_filter_setbyindex(f, pidx, value);
                break;
        }
    }
    return res;
}

static int setup_chain_buffer(struct fg_effect_chain* chain, struct gcsynth_filter_graph* fg, int channel)
{
    int sample_count = 1;

    switch(chain->chain_pass_type) {
        // no band pass filters
        case EFFECT_CHAIN_ALLPASS:
            // copy input to working buffer for filter chain.
            memcpy(chain->left, fg->in_left, sizeof(chain->left));
            memcpy(chain->right, fg->in_right, sizeof(chain->right));
            break;

        case EFFECT_CHAIN_BANDPASS:
            sample_count = fg_bandpass_filter(channel, 
                    chain->low_freq, 
                    chain->high_freq, 
                    chain->left, 
                    chain->right);
            
            break;

        case EFFECT_CHAIN_LOWPASS:
            sample_count = fg_lowpass_filter(channel, 
                    chain->freq, 
                    chain->left, 
                    chain->right);
            break;

        case EFFECT_CHAIN_HIGHPASS:
            sample_count = fg_highpass_filter(channel, 
                    chain->freq, 
                    chain->left, 
                    chain->right);
            break;
    }// end switch 
    
    return sample_count > 0;
}


static void fchain_apply_effects(struct fg_effect_chain *chain)
{
    GList* iter;

    for(iter = g_list_first(chain->effects); iter != NULL; iter = iter->next) {
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
        if (f->enabled) {
            gcsynth_filter_run_sterio(f, chain->left, chain->right, AUDIO_SAMPLES);
        }
    }
}


void pre_demux_proc(struct gcsynth_filter_graph* fg, float* left, float* right)
{
    GList* iter;

    for(iter = g_list_first(fg->pre_demux_effects);
        iter != NULL;
        iter = iter->next
    ) {
        struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data;
        // apply filter to audio buffers
        if (f->enabled) {
            gcsynth_filter_run_sterio(f, left, right, AUDIO_SAMPLES);
        }
    }
}


/**
 * Process in_left/right buffers for each filter chain, 
 * 
 */
void demux_proc(struct gcsynth_filter_graph* fg, int channel) 
{
    int chain_num;
    int sample_count;
    
    // run each filter chain 
    for(chain_num = 0; fg->demuxer.num_chains; chain_num++) {
        struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_num];

        // setup the filter chain buffer, apply optional band pass filters 
        int allow_chain_proc = (chain->enabled) ?
            setup_chain_buffer( chain, fg, channel ): 0;

        if (allow_chain_proc) {
            chain->populated = 1;
            // apply audio effects to this filter chain
            fchain_apply_effects(chain);
            // apply optional balance/gain
            fg_proc_balance_gain(chain->balance, 
                chain->gain, chain->left, chain->right);
        } else {
            chain->populated = 0;
        }
    }
}

void fg_demux_enable_chain(struct gcsynth_filter_graph* fg, int chain_idx, int enable)
{
    if (chain_idx >= 0 && chain_idx < MAX_FILTER_CHAINS) {
        fg->demuxer.effect_chains[chain_idx].enabled = enable;
    }
}

void fg_demux_num_chains(struct gcsynth_filter_graph* fg, int num_chains) {
    if (num_chains >= 0 && num_chains < MAX_FILTER_CHAINS) {
        fg->demuxer.num_chains = num_chains;
    }
}

void fg_demux_chain_balance(struct gcsynth_filter_graph* fg, int chain_idx, float balance)
{
    if (chain_idx >= 0 && chain_idx < MAX_FILTER_CHAINS) {
        fg->demuxer.effect_chains[chain_idx].balance = balance;
    }
}

void fg_demux_chain_gain(struct gcsynth_filter_graph* fg, int chain_idx, float gain)
{
    if (chain_idx >= 0 && chain_idx < MAX_FILTER_CHAINS) {
        fg->demuxer.effect_chains[chain_idx].gain = gain;
    }
}


int fg_demux_set_param_byname(struct gcsynth_filter_graph* fg, int chain_idx,
    char* label, char* name, float value)
{
    return fg_demux_set_param(fg, chain_idx,
        label, PARAM_BY_NAME, name, 0, value);
}

int fg_demux_set_param_byindex(struct gcsynth_filter_graph* fg, int chain_idx,
    char* label, int pidx, float value)
{
    return fg_demux_set_param(fg, chain_idx,
        label, PARAM_BY_INDEX, "", pidx, value);
}

