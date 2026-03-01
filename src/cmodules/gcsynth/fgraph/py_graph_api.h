#ifndef __PY_GRAPH_API
#define __PY_GRAPH_API

/**
 * Integrate with the gcsynth.c module to expose an api for the application
 * to manipulate audio filter graphs.
 * 
 */
#include <Python.h>
#include "fgraph/fgraph.h"

enum
{
    FG_API_DESTROY,
    FG_API_CREATE,
    FG_API_ENABLE,
    FG_API_DISABLE,
    FG_API_ASSIGN_TO_CHANNEL,
    FG_API_UNASSIGN_TO_CHANNEL,
    FG_API_ADD_NODE,
    FG_API_REMOVE_NODE,
    FG_API_ADD_CONNECTION,
    FG_API_REMOVE_CONNECTION,
    FG_API_SET_ATTR,


    FGRAPH_PY_API_NUMCOMMANDS
};

/**
 * opcode, operator type interface using numeric IDs and arguments.
 */
PyObject* py_fgraph_api(PyObject* self, PyObject* args);

// allow for initialization
int init_filter_graph_subsys(PyObject *module);




#endif