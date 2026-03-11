#ifndef __BANDPASS_H
#define __BANDPASS_H    

#include "fgraph/fgraph.h"

void bandpass_run(struct fgraph_node* node, float* left, float* right);
void lowpass_run(struct fgraph_node* node, float* left, float* right);
void highpass_run(struct fgraph_node* node, float* left, float* right);

void fg_set_band_attribute(struct fgraph_node *node, 
    int att_id, 
    int ival,
    float fval, 
    char* sval);



#endif