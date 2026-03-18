#include <Python.h>
#include "py_graph_api.h"
#include "fgraph.h"
#include "gcsynth_sf.h"


#include <stdlib.h>
#include <stdio.h>




/*
    Module interface 
 */

static int get_command_id(PyObject* args)
{
    int cmd = -1;

    if (PyTuple_GET_SIZE(args) > 0) {
        PyObject* item = PyTuple_GetItem(args, 0);
        if (PyLong_Check(item)) {
            cmd = (int) PyLong_AsLong(item);
        }
    }

    return cmd;
}

PyObject* py_fgraph_api(PyObject* self, PyObject* args)
{
    int cmd = get_command_id(args);

    switch(cmd) {
        case FG_API_DESTROY: {
                char* uuid;
                if (!PyArg_ParseTuple(args,"is", &cmd, &uuid)) {
                    return NULL;
                }
                fg_destroy(uuid);
            }
            break;
        case FG_API_CREATE: {
                char* uuid;
                if (!PyArg_ParseTuple(args,"is", &cmd, &uuid)) {
                    return NULL;
                }
                fg_create(uuid);
            }
            break;
        case FG_API_ENABLE:{
                char* uuid;
                int enabled=1;
                if (!PyArg_ParseTuple(args,"is", &cmd, &uuid)) {
                    return NULL;
                }
                fg_set_enable(uuid, enabled);
            }
            break;
        case FG_API_DISABLE:{
                char* uuid;
                int enabled=0;
                if (!PyArg_ParseTuple(args,"is", &cmd, &uuid)) {
                    return NULL;
                }
                fg_set_enable(uuid, enabled);
            }
            break;
        case FG_API_ADD_NODE: {
                char* fg_uuid;
                char* node_uuid;
                int node_type;

                if (!PyArg_ParseTuple(args,"issi", &cmd, &fg_uuid, &node_uuid, &node_type)) {
                    return NULL;
                }
                if (fg_create_node(fg_uuid, node_uuid, node_type) == -1) {
                    fprintf(stderr,"%s\n", "fg_create_node failed!");
                    return NULL;
                }
            }
            break;   
        case FG_API_REMOVE_NODE: {
                char* fg_uuid;
                char* node_uuid;

                if (!PyArg_ParseTuple(args,"iss", &cmd, &fg_uuid, &node_uuid)) {
                    return NULL;
                }
                fg_delete_node(fg_uuid, node_uuid);
                
            }
            break;
        
        case FG_API_SET_ATTR:
            {
                char* graph_uuid;
                char* node_uuid;
                int type;
                int att_id;
                PyObject* val;
                int ival = 0;
                float fval = 0.0;
                char* sval = "";
                int overflow;

                
                if (!PyArg_ParseTuple(args,"issiiO", &cmd, &graph_uuid, &node_uuid, &type, &att_id, &val)) {
                    return NULL;
                }

                if (PyLong_Check(val)) {
                    ival = (int) PyLong_AsLongAndOverflow(val, &overflow);
                }
                if (PyFloat_Check(val)) {
                    fval = (float) PyFloat_AsDouble(val);
                }
                if (PyUnicode_Check(val)) {
                    sval = (char*) PyUnicode_AsUTF8(val);  
                }

                fg_set_node_attribute(graph_uuid, node_uuid, type, 
                    att_id, ival, fval,  sval);
                
            }
            break;
        case FG_API_EFFECT_SET_PROPERTY: {
            char* fg_uuid;
            char* effect_uuid;
            char* prop_name;
            float value;
            
            if (!PyArg_ParseTuple(args,"isssf", &cmd, &fg_uuid, &effect_uuid, &prop_name, &value)) {
                return NULL;
            }

            if (fg_set_effect_property(fg_uuid, effect_uuid, prop_name, value) == -1) {
                return NULL;
            }

        } 
            break;

        case FG_API_EFFECT_SETUP: {
            char* fg_uuid;
            char* effect_uuid;
            char* label;
            char* path;

            if (!PyArg_ParseTuple(args,"issss", &cmd, &fg_uuid, &effect_uuid, &path, &label)) {
                return NULL;
            }

            // load ladspa audio effect.            
            if (fg_setup_effect(fg_uuid, effect_uuid, path, label) == -1) {
                return NULL;
            }

        }
            break;
        case FG_API_ADD_CONNECTION: {
                char* fg_uuid;
                char* conn_uuid;
                char* input_uuid;
                int input_port;
                char* output_uuid;
                int output_port;


                if (!PyArg_ParseTuple(args,"isssisi", 
                    &cmd, 
                    &fg_uuid, 
                    &conn_uuid, 
                    &input_uuid,
                    &input_port,
                    &output_uuid,
                    &output_port))  {
                    return NULL;
                }

                if (fg_connect_nodes(fg_uuid, conn_uuid, input_uuid, input_port, output_uuid, output_port) == -1) {
                    fprintf(stderr,"%s\n", "fg_connect_nodes failed!");
                    return NULL;
                }

            }
            break;
        case FG_API_ASSIGN_TO_CHANNEL:
            break;
        case FG_API_UNASSIGN_TO_CHANNEL:
            break;
        case -1:
            fprintf(stderr,"Unable to parse get command id\n");
            gcsynth_raise_exception("Unable to parse get command id\n");
            return NULL;
        default:
            gcsynth_raise_exception("Unknown command!");
            return NULL;
    }

    Py_RETURN_NONE;
}

// allow for initialization
int init_filter_graph_subsys(PyObject *module)
{

    PyModule_AddIntConstant(module, "FG_API_DESTROY", FG_API_DESTROY);
    PyModule_AddIntConstant(module, "FG_API_CREATE", FG_API_CREATE);
    PyModule_AddIntConstant(module, "FG_API_ENABLE", FG_API_ENABLE);
    PyModule_AddIntConstant(module, "FG_API_DISABLE", FG_API_DISABLE);
    PyModule_AddIntConstant(module, "FG_API_ASSIGN_TO_CHANNEL", FG_API_ASSIGN_TO_CHANNEL);
    PyModule_AddIntConstant(module, "FG_API_UNASSIGN_TO_CHANNEL", FG_API_UNASSIGN_TO_CHANNEL);
    PyModule_AddIntConstant(module, "FG_API_ADD_NODE", FG_API_ADD_NODE);
    PyModule_AddIntConstant(module, "FG_API_REMOVE_NODE", FG_API_REMOVE_NODE);
    PyModule_AddIntConstant(module, "FG_API_ADD_CONNECTION", FG_API_ADD_CONNECTION);
    PyModule_AddIntConstant(module, "FG_API_REMOVE_CONNECTION", FG_API_REMOVE_CONNECTION);
    PyModule_AddIntConstant(module, "FG_API_EFFECT_SETUP", FG_API_EFFECT_SETUP);

    PyModule_AddIntConstant(module, "FG_NODE_TYPE_LOWPASS", FG_NODE_TYPE_LOWPASS);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_HIGHPASS", FG_NODE_TYPE_HIGHPASS);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_BANDPASS", FG_NODE_TYPE_BANDPASS);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_EFFECT", FG_NODE_TYPE_EFFECT);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_INPUT", FG_NODE_TYPE_INPUT);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_OUTPUT", FG_NODE_TYPE_OUTPUT);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_MIXER", FG_NODE_TYPE_MIXER);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_SPLITTER", FG_NODE_TYPE_SPLITTER);
    PyModule_AddIntConstant(module, "FG_NODE_TYPE_GAIN_BALANCE", FG_NODE_TYPE_GAIN_BALANCE);
    PyModule_AddIntConstant(module, "FG_API_SET_ATTR", FG_API_SET_ATTR);


    PyModule_AddIntConstant(module, "AID_ENABLE_FALLBACK_METHOD", AID_ENABLE_FALLBACK_METHOD);
    PyModule_AddIntConstant(module, "AID_DISABLE_FALLBACK_METHOD", AID_DISABLE_FALLBACK_METHOD);
    PyModule_AddIntConstant(module, "AID_GAIN", AID_GAIN);
    PyModule_AddIntConstant(module, "AID_BALANCE", AID_BALANCE);
    PyModule_AddIntConstant(module, "AID_LOW_PASS_FREQ", AID_LOW_PASS_FREQ);    
    PyModule_AddIntConstant(module, "AID_HIGH_PASS_FREQ", AID_HIGH_PASS_FREQ);
    PyModule_AddIntConstant(module, "AID_BAND_PASS_LOW_FREQ", AID_BAND_PASS_LOW_FREQ);
    PyModule_AddIntConstant(module, "AID_BAND_PASS_HIGH_FREQ", AID_BAND_PASS_HIGH_FREQ);
    PyModule_AddIntConstant(module, "AID_ENABLE", AID_ENABLE);
    PyModule_AddIntConstant(module, "AID_DISABLE", AID_DISABLE);

    return fg_init();
}

