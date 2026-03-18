#include "mixer.h"

#include <stdio.h>

int mixer_run(struct fgraph_node* node, float* left, float* right)
{
    GList* iter = g_list_first(node->out_ports);
    struct fgraph_connection* out = (iter) ? ((struct fgraph_connection*) iter->data): NULL;
    int i;
    char errmsg[256];

    errmsg[0] = '\0';

    if (out == NULL) {
        sprintf(errmsg,"mixer_run: node %s, Unable to get a connection on the output port\n",
            node->base.uuid);
        gcsynth_raise_exception(errmsg);
    } else {
        for(i = 0; i < AUDIO_SAMPLES; i++) {
            out->left[i] = 0.0;
            out->right[i] = 0.0;
        }


        for (iter = g_list_first(node->in_ports);
            iter != NULL;
            iter = iter->next )
        {
            struct fgraph_connection* c = (struct fgraph_connection*) iter->data;
            if (c == NULL) {
                sprintf(errmsg,"mixer_run: node %s, Unable to get a connection on the input port\n",
                    node->base.uuid);
                gcsynth_raise_exception(errmsg);
                break; // exit forloop
            }

            for(i = 0; i < AUDIO_SAMPLES; i++) {
                out->left[i] += c->left[i];
                out->right[i] += c->right[i];
            }
        }
    }

    return (errmsg[0] == '\0') ? 0: -1;
}
