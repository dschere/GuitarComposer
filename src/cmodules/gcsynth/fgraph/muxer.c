#include "../gcsynth_filter_graph.h"


/**
 * Mix all filter chains to output buffer
 */
void muxer_proc(struct gcsynth_filter_graph* fg)
{
    int chain_idx;
    int count = 0;
    int i;

    for(chain_idx = 0; chain_idx < fg->demuxer.num_chains; chain_idx++) {
        struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_idx];

        if (chain->populated) {
            if (count == 0) {
                for(i = 0; i < AUDIO_SAMPLES; i++) {
                    fg->out_left[i] = chain->left[i];
                    fg->out_right[i] = chain->right[i];
                }
            } else {
                for(i = 0; i < AUDIO_SAMPLES; i++) {
                    fg->out_left[i] += chain->left[i];
                    fg->out_right[i] += chain->right[i];
                }
            }
            count++;
        }
    }
}
