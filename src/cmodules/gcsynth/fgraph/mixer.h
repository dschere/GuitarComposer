#ifndef __MIXER_H
#define __MIXER_H

#include "fgraph.h"

void mixer_run(struct fgraph_node* node, float* left, float* right);

#endif