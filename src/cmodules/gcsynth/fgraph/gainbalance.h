#ifndef __GAINBALANCE_H
#define __GAINBALANCE_H

#include "fgraph.h" 

int gainbalance_run(struct fgraph_node* node, float* left, float* right);


void fg_set_gb_attribute(struct fgraph_node *node, 
    int att_id, 
    int ival,
    float fval, 
    char* sval);

#endif
