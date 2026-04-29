#include "gainbalance.h"

#include <assert.h>

void fg_set_gb_attribute(struct fgraph_node *node, 
    int att_id, 
    int ival,
    float fval, 
    char* sval)
{
    struct fgraph_gain_balance* gb = (struct fgraph_gain_balance*) node;
    
    assert(node->base.type == FG_NODE_TYPE_GAIN_BALANCE);
    switch(att_id) {
        case AID_GAIN:
            gb->gain = fval;
            break;
        case AID_BALANCE:
            gb->balance = fval;
            break;
        default:
    }
}


int gainbalance_run(struct fgraph_node* node, float* left, float* right)
{
    struct fgraph_gain_balance* gb = (struct fgraph_gain_balance*) node;
    
    assert(node->base.type == FG_NODE_TYPE_GAIN_BALANCE);

    if (gb->gain != 1.0) {
        int i;
        for(i = 0; i < AUDIO_SAMPLES; i++) {
            left[i] *= gb->gain;
            right[i] *= gb->gain;
        }
    }

    if (gb->balance != 1.0) {
        int i;
        float left_mu, right_mu;

        if (gb->balance > 1.0) {
            left_mu = 1.0 + (gb->balance - 1.0);
            right_mu = 1.0 + (1.0 - gb->balance); 
        } else { // balance < 1.0
            right_mu = 1.0 + gb->balance;
            left_mu = 1.0  - gb->balance; 
        }

        for(i = 0; i < AUDIO_SAMPLES; i++) {
            left[i] *= left_mu;
            right[i] *= right_mu;
        }
    }
    
    return 0;
}
