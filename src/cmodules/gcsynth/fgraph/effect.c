#include <stdio.h>

#include "effect.h"
#include "gcsynth_filter.h"

int fg_effect_run(struct fgraph_node* node, float* left, float* right)
{
    int ret = 0;
    struct fgraph_effect* e = (struct fgraph_effect*) node;

    if ((e->filter != NULL) && (e->filter->enabled == 1)) {
        ret = gcsynth_filter_run_sterio(e->filter, left, right, AUDIO_SAMPLES);
    }

    return ret;
}
