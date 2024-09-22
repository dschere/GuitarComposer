#include <Python.h>
/**
 * This module is the data exchange between python and c routines. its job is to
 * decode the python input_dict (a PyDict object and make calls to other modules)
 * 
 */

#include "gcsynth.h"

static PyObject *GcsynthException = NULL;
static struct gcsynth GcSynth;

// decoding routines
static void gcsynth_start_args_init(
    struct gcsynth_start_cfg* args, 
    PyObject* input_dict,
    char* errmsg
);



// api

void gcsynth_raise_exception(char* errmsg) {
    if (GcsynthException) {
        PyErr_SetString(GcsynthException, errmsg);
    }
}

// Function to handle Python dictionary input
static PyObject* py_gcsynth_start(PyObject* self, PyObject* args) {
    PyObject* input_dict;
    char errmsg[ERRMSG_SIZE];
    struct gcsynth_start_cfg cfg = { .num_sfpaths = 0 };
    int i;

    // Parse the Python dictionary from the argument
    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &input_dict)) {
        return NULL; // If parsing fails, return NULL
    }

    errmsg[0] = '\0';
    gcsynth_start_args_init(&cfg, input_dict, errmsg);
    if (errmsg[0]) {
        gcsynth_raise_exception(errmsg);
        return NULL;
    }

    // call gcsynth_start(&cfg)
    

    if (cfg.test) {
        printf("num_sfpaths = %d\n",cfg.num_sfpaths);
        for(i = 0; i < cfg.num_sfpaths; i++) {
            printf("   cfg.sfpaths[%d] = %s\n",i, cfg.sfpaths[i]);
        }
    }

    // cleanup
    for(i = 0; i < cfg.num_sfpaths; i++) {
        free(cfg.sfpaths[i]);
    }

    Py_RETURN_NONE; // Return None to Python
}


static void gcsynth_start_args_init(
    struct gcsynth_start_cfg* cfg, 
    PyObject* input_dict,
    char* errmsg
)
{
    int i;

    // are we running in test mode?
    cfg->test = (PyDict_GetItemString(input_dict, "test") != NULL); 

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
    {"start", py_gcsynth_start, METH_VARARGS, "Start the gcsynth."},
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
