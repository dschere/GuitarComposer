#include <Python.h>
/**
 * This module is the data exchange between python and c routines. its job is to
 * decode the python input_dict (a PyDict object and make calls to other modules)
 * 
 */

#include "gcsynth.h"
#include "gcsynth_filter.h"
#include "gcsynth_channel.h"

static PyObject *GcsynthException = NULL;
static struct gcsynth GcSynth;



// decoding routines
static void gcsynth_start_args_init(
    struct gcsynth_cfg* args, 
    PyObject* input_dict,
    char* errmsg
);



// api

void gcsynth_raise_exception(char* errmsg) {
    if (GcsynthException) {
        PyErr_SetString(GcsynthException, errmsg);
    }
}


static PyObject* py_filter_test(PyObject* self, PyObject* args) {
    const char* filepath;
    const char* plugin_name;
    struct gcsynth_filter* filter = NULL;
    int i;
    int changed = 0;
    int test_passed;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "ss", &filepath, &plugin_name)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    // load plugin
    filter = gcsynth_filter_new_ladspa(filepath, (char*)plugin_name);
    if (filter == NULL) {
        return NULL;
    }

    // send a square wave in and verify that the wave out has changed. 
    //TODO implement a better clever audio analysis probably run the
    // the tests that the author who created the ladspa filter did.
    if (filter->in_buf_count == 0) {
        gcsynth_raise_exception("test requires a filter with an input!");
        return NULL;
    } 

    for(i = 0; i < FLUID_BUFSIZE; i++) {
        if ((i/8) % 2) {
            filter->in_data_buffer[0][i] = 100.0;
            filter->out_data_buffer[0][i] = 0.0;
        } else {
            filter->in_data_buffer[0][i] = 0;
        }
    }

    // run filter
    filter->desc->run(filter->plugin_instance, SAMPLE_RATE);

    for(i = 0; (i < FLUID_BUFSIZE) && (changed == 0); i++) {
        if ((i/8) % 2) {
            float d = filter->out_data_buffer[0][i];
            if ((d != 0.0) && (d != 100.0)) {
                changed = 1;
            }
        } 
    }    

    // unload plugin
    gcsynth_filter_destroy(filter);

    test_passed = changed;    
    return PyBool_FromLong(test_passed);
}

static PyObject* py_query_filter(PyObject* self, PyObject* args) {
    const char* filepath;
    const char* plugin_name;
    PyObject* control_info_list = NULL;
    struct gcsynth_filter* filter = NULL;
    int i;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "ss", &filepath, &plugin_name)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    // load plugin
    filter = gcsynth_filter_new_ladspa(filepath,(char*) plugin_name);
    if (filter == NULL) {
        return NULL;
    }

    // gather information for controls
    control_info_list = PyList_New(filter->num_controls); 
    for(i = 0; i < filter->num_controls; i++) {
        struct gcsynth_filter_control* c = &filter->controls[i];
        PyObject* item = PyDict_New();

        PyDict_SetItemString(item,"c_index",PyLong_FromLong(i));

        PyDict_SetItemString(item,
            "has_default", PyBool_FromLong(c->has_default));
        PyDict_SetItemString(item, 
            "default_value",PyFloat_FromDouble((double) c->default_value));
            
        PyDict_SetItemString(item, 
            "upper_bound", PyFloat_FromDouble((double)c->upper));
        PyDict_SetItemString(item, 
            "lower_bound", PyFloat_FromDouble((double)c->lower));

        PyDict_SetItemString(item,
            "name", PyUnicode_FromString(c->name));
        PyDict_SetItemString(item,
            "is_bounded_above", PyBool_FromLong(c->is_bounded_above));    
        PyDict_SetItemString(item,
            "is_bounded_below", PyBool_FromLong(c->is_bounded_below));
        PyDict_SetItemString(item,
            "is_integer", PyBool_FromLong(c->is_integer));
        PyDict_SetItemString(item,
            "is_logarithmic", PyBool_FromLong(c->is_logarithmic));
        PyDict_SetItemString(item,
            "is_toggled", PyBool_FromLong(c->is_toggled));
      
        PyList_SetItem(control_info_list, i, item); 
    }

    // unload plugin
    gcsynth_filter_destroy(filter);

    //return data
    return control_info_list;
}

static PyObject* py_load_ladspa_filter(PyObject* self, PyObject* args) {
    int channel;
    const char* filepath;
    const char* plugin_name;
    PyObject* controls_dict;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "iss|O!", &channel, &filepath, &plugin_name,
        &PyDict_Type, &controls_dict)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    if (channel < 0 || channel >= MAX_CHANNELS) {
        gcsynth_raise_exception("channel must be between 0-64");
        return NULL;
    }

    // setup controls values if present, these will initialize plugin
     


    Py_RETURN_NONE;
}



static PyObject* py_gcsynth_stop(PyObject* self, PyObject* args) {
    gcsynth_stop(&GcSynth);
    Py_RETURN_NONE;
}

// Function to handle Python dictionary input
static PyObject* py_gcsynth_start(PyObject* self, PyObject* args) {
    PyObject* input_dict;
    char errmsg[ERRMSG_SIZE];
    int i;

    GcSynth.cfg.num_sfpaths = 0;
    GcSynth.cfg.num_midi_channels = NUM_CHANNELS; 

    // Parse the Python dictionary from the argument
    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &input_dict)) {
        return NULL; // If parsing fails, return NULL
    }

    errmsg[0] = '\0';
    gcsynth_start_args_init(&GcSynth.cfg, input_dict, errmsg);
    if (errmsg[0]) {
        gcsynth_raise_exception(errmsg);
        return NULL;
    }


    if (GcSynth.cfg.test) {
        printf("num_sfpaths = %d\n",GcSynth.cfg.num_sfpaths);
        for(i = 0; i < GcSynth.cfg.num_sfpaths; i++) {
            printf("   cfg.sfpaths[%d] = %s\n",i, GcSynth.cfg.sfpaths[i]);
        }
    } else {
        // not a test 
        gcsynth_start(&GcSynth);
    }

    // cleanup
    for(i = 0; i < GcSynth.cfg.num_sfpaths; i++) {
        free(GcSynth.cfg.sfpaths[i]);
    }

    Py_RETURN_NONE; // Return None to Python
}





static long PyDict_GetItemLong(PyObject* dict, char* key, int defval)
{
    PyObject* item = PyDict_GetItemString(dict,key);
    long result = defval;
    if (item && PyLong_Check(item)) {
        result = PyLong_AsLong(item);
    }
    return result;
}


static void gcsynth_start_args_init(
    struct gcsynth_cfg* cfg, 
    PyObject* input_dict,
    char* errmsg
)
{
    int i;

    // are we running in test mode?
    cfg->test = (PyDict_GetItemString(input_dict, "test") != NULL); 
    cfg->num_midi_channels = (int) PyDict_GetItemLong(input_dict,"num_channels",NUM_CHANNELS);

    PyObject* py_list = PyDict_GetItemString(input_dict, "sfpaths");
    if ((py_list != NULL) && PyList_Check(py_list)) {

        // Get the size of the list
        cfg->num_sfpaths = (int) PyList_Size(py_list);

        // Iterate over the list
        for (i = 0; (i < cfg->num_sfpaths) && (i < MAX_SOUNDFONTS); i++) {
            // Get the item at index `i` (as a PyObject*)
            PyObject* pyItem = PyList_GetItem(py_list, i);

            // Check if the item is a string
            if (PyUnicode_Check(pyItem)) {
                // Convert the Python string to a C string (UTF-8 encoded)
                const char *spath = PyUnicode_AsUTF8(pyItem);
                if (spath != NULL) {
                    cfg->sfpaths[i] = strdup(spath);
                } else {
                    sprintf(errmsg,"start() command sfpaths[%d] PyUnicode_AsUTF8 failed", i);    
                }
            } else {
                sprintf(errmsg,"start() command sfpaths[%d] is not a string", i);        
            }
            Py_XDECREF(pyItem);
        }
        Py_XDECREF(py_list);
    } else {
        sprintf(errmsg,"start() command missing sfpaths or its not a list");
    }
    
}





// ------------ interface for moduler loader in python




// Define the methods of the module
static PyMethodDef GCSynthMethods[] = {
    {"stop", py_gcsynth_stop, METH_NOARGS, "Stop synth."},
    {"start", py_gcsynth_start, METH_VARARGS, "Start the gcsynth."},
    {"add_filter",py_load_ladspa_filter, METH_VARARGS,"create a filter for a channel"},
    {"query_filter",py_query_filter, METH_VARARGS,"py_query_filter(path,plugin_name)->[{info}]"},
    {"test_filter",py_filter_test,METH_VARARGS,"test_filter(path,plugin_name)-> pass/fail test"},
    {NULL, NULL, 0, NULL}
};

// Define the module itself
static struct PyModuleDef gcsynthmodule = {
    PyModuleDef_HEAD_INIT,
    "gcsynth",  // Module name
    NULL,       // Module documentation
    -1,         // Size of per-interpreter state (-1 = global state)
    GCSynthMethods
};

// Initialization function
PyMODINIT_FUNC PyInit_gcsynth(void) {
    // Create the custom exception
    GcsynthException = PyErr_NewException("gcsynth.GcsynthException", NULL, NULL);
    Py_INCREF(GcsynthException);

    // Create the module object
    PyObject *module = PyModule_Create(&gcsynthmodule);
    if (module == NULL) {
        return NULL;
    }

    // Add the custom exception to the module
    PyModule_AddObject(module, "GcsynthException", GcsynthException);
    return module;
}
