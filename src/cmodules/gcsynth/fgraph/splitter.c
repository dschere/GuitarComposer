#include "splitter.h"

#include <stdio.h>


/**
 * Split audio into output port buffers
 */
int splitter_run(struct fgraph_node* node, float* left, float* right)
{
    int num_outports = g_list_length( node->out_ports );
    float level;
    int i;
    GList* iter;

    if (num_outports == 0) {
        char errmsg[256];

        sprintf(errmsg,"splitter_run node %s, no output ports!\n", node->base.uuid);
        gcsynth_raise_exception(errmsg);
        return -1;
    }

    level = 1.0 / num_outports;

    for(iter = g_list_first(node->out_ports);
        iter != NULL;
        iter = iter->next
    ) {
        struct fgraph_connection* conn = (struct fgraph_connection*) iter->data;
        for(i = 0; i < AUDIO_SAMPLES; i++) {
            conn->left[i] = left[i] * level;
            conn->right[i] = right[i] * level;
        }
        node->in_port_update_count++;
    }

    return 0;
}
