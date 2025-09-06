#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <errno.h>

#include <Python.h>
#include <SDL2/SDL.h>


/**
 * This module is the data exchange between python and c routines. its job is to
 * decode the python input_dict (a PyDict object and make calls to other modules)
 * 
 */

#include "gcsynth.h"
#include "gcsynth_filter.h"
#include "gcsynth_channel.h"
#include "gcsynth_event.h"
#include "pyutil.h"
#include "gcsynth_acapture.h"



static PyObject *GcsynthException = NULL;
static struct gcsynth GcSynth;


#define PyDict_SetItemString2(dict, key, py_value) \
    {PyDict_SetItemString(dict,key,py_value); Py_DECREF(py_value);}    

#define CHECK_CHANNEL_VALUE(channel) \
    if (channel < 0 || channel >= NUM_CHANNELS) { \
        char msg[256]; \
        sprintf(msg,"channel %d needs to be within 0 and %d\n", \
             channel, NUM_CHANNELS); \
        raise_value_error(msg); \
        return NULL; \
    } 


// decoding routines
static void gcsynth_start_args_init(
    struct gcsynth_cfg* args, 
    PyObject* input_dict,
    char* errmsg
);

//static struct scheduled_event* scheduled_event_new(PyObject* dict);


// api

void gcsynth_raise_exception(char* errmsg) {
    if (GcsynthException) {
        fprintf(stderr,"gcsynth_raise_exception %s\n", errmsg);
        PyErr_SetString(GcsynthException, errmsg);
    }
}



static PyObject* py_filter_test(PyObject* self, PyObject* args) {
    const char* filepath;
    const char* plugin_label;
    struct gcsynth_filter* filter = NULL;
    int i;
    int changed = 0;
    LADSPA_Data io_buffer[FLUID_BUFSIZE];

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "ss", &filepath, &plugin_label)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    // load plugin
    filter = gcsynth_filter_new_ladspa(filepath, (char*)plugin_label);
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

    // create a square wave 
    for(i = 0; i < FLUID_BUFSIZE; i++) {
        if ((i/8) % 2) {
            io_buffer[i] = 100.0;
        } else {
            io_buffer[i] = 0.0;
        }
    }

    gcsynth_filter_run(filter, io_buffer, FLUID_BUFSIZE);
    
    // should have altered the io_buffer
    for(i = 0; (i < FLUID_BUFSIZE) && (changed == 0); i++) {
        if ((i/8) % 2) {
            if (io_buffer[i] != 100.0) {
                changed = 1;
            }
        } else {
            if (io_buffer[i] != 0.0) {
                changed = 1;
            }
        }
    }

    // unload plugin
    gcsynth_filter_destroy(filter);

    // now let's test the set methods for a control
    if (changed == 0) {
        gcsynth_raise_exception("filter test failed!\n");
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject* py_start_capture(PyObject* self, PyObject* args) {
    char* device;
    int result;

    if (!PyArg_ParseTuple(args, "s", &device)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    result = StartAudioCapture(device);
    return PyLong_FromLong(result);
}

static PyObject* py_stop_capture(PyObject* self, PyObject* args) {
    StopAudioCapture();
    Py_RETURN_NONE;
}

static PyObject* py_list_capture_devices(PyObject* self, PyObject* args) {
    int num = SDL_GetNumAudioDevices(1);
    PyObject* device_name_list = NULL;
    int id;

    if (num < 1) {
        device_name_list = PyList_New(0);
    } else {
        device_name_list = PyList_New( num );
        for (id = 0; id < num; id++) {
            PyObject* item;
            char noname[256];
            const char *name = SDL_GetAudioDeviceName(id, 1);

            if (name) {
                item = PyUnicode_FromString(name);
            } else {
                sprintf(noname,"noname-capture-%d",id);
                item = PyUnicode_FromString( noname);
            }
            
            Py_INCREF(item);
            PyList_SetItem(device_name_list, id, item);
            
        }
    }

    Py_INCREF(device_name_list);
    return device_name_list;
}

static PyObject* py_query_filter(PyObject* self, PyObject* args) {
    const char* filepath;
    const char* plugin_label;
    PyObject* control_info_list = NULL;
    struct gcsynth_filter* filter = NULL;
    int i;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "ss", &filepath, &plugin_label)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    // load plugin
    filter = gcsynth_filter_new_ladspa(filepath,(char*) plugin_label);
    if (filter == NULL) {
        return NULL;
    }


    // gather information for controls
    control_info_list = PyList_New(filter->num_controls); 
    for(i = 0; i < filter->num_controls; i++) {
        struct gcsynth_filter_control* c = &filter->controls[i];
        PyObject* item = PyDict_New();

        PyDict_SetItemString2(item,"c_index",PyLong_FromLong(i));

        PyDict_SetItemString2(item,
            "has_default", PyBool_FromLong(c->has_default));
        PyDict_SetItemString2(item, 
            "default_value",PyFloat_FromDouble((double) c->default_value));
            
        PyDict_SetItemString2(item, 
            "upper_bound", PyFloat_FromDouble((double)c->upper));
        PyDict_SetItemString2(item, 
            "lower_bound", PyFloat_FromDouble((double)c->lower));

        PyDict_SetItemString2(item,
            "name", PyUnicode_FromString(c->name));
        PyDict_SetItemString2(item,
            "is_bounded_above", PyBool_FromLong(c->is_bounded_above));    
        PyDict_SetItemString2(item,
            "is_bounded_below", PyBool_FromLong(c->is_bounded_below));
        PyDict_SetItemString2(item,
            "is_integer", PyBool_FromLong(c->is_integer));
        PyDict_SetItemString2(item,
            "is_logarithmic", PyBool_FromLong(c->is_logarithmic));
        PyDict_SetItemString2(item,
            "is_toggled", PyBool_FromLong(c->is_toggled));

        Py_INCREF(item);
        PyList_SetItem(control_info_list, i, item);
    }

    // unload plugin
    gcsynth_filter_destroy(filter);

    Py_INCREF(control_info_list);

    //return data
    return control_info_list;
}

static PyObject* py_channel_gain(PyObject* self, PyObject* args) {
    int channel;
    float gain;

    if (!PyArg_ParseTuple(args, "if", &channel, &gain)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_channel_gain(channel, gain);

    Py_RETURN_NONE;
}

static PyObject* py_gcsynth_channel_enable_filter(PyObject* self, PyObject* args) {
    int channel;
    char* plugin_label;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "is", &channel, &plugin_label)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_channel_enable_filter(channel, plugin_label);

    Py_RETURN_NONE;
}


static PyObject* py_gcsynth_channel_disable_filter(PyObject* self, PyObject* args) {
    int channel;
    char* plugin_label;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "is", &channel, &plugin_label)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_channel_disable_filter(channel, plugin_label);

    Py_RETURN_NONE;
}

static PyObject* py_gcsynth_event(PyObject* self, PyObject* args) {
    PyObject* event_params;
    struct scheduled_event* s_event;
    PyObject* evt_id_list = NULL;

    if (!PyArg_ParseTuple(args,"O",&event_params)) {
        return NULL;
    }

    if (PyDict_Check(event_params)) {
        s_event = event_from_pydata(event_params);
        if (s_event) {
            evt_id_list = PyList_New(1);

            gcsynth_schedule(&GcSynth, s_event);

            PyObject *py_evt_id = PyLong_FromLong(s_event->event_id);
            if (!py_evt_id) {
                return NULL;
            }
            PyList_SET_ITEM(evt_id_list, 0, py_evt_id);
        } else {
            return NULL;
        }
    }
    else if (PyList_Check(event_params)) {
        PyObject* list = event_params;
        Py_ssize_t size = PyList_Size(list);

        evt_id_list = PyList_New(size);

        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject *item = PyList_GetItem(list, i);  // Borrowed reference
            s_event = event_from_pydata(item);
            if (s_event) {
                gcsynth_schedule(&GcSynth, s_event);
                PyObject *py_evt_id = PyLong_FromLong(s_event->event_id);
                if (!py_evt_id) {
                    return NULL;
                }
                PyList_SET_ITEM(evt_id_list, i, py_evt_id);

            } else {
                return NULL;
            }
        }
    }
    else {
        gcsynth_raise_exception(
  "gcsynth_event expects either list of dictionaries or a single dictionary."
        );
        return NULL;
    }

    return evt_id_list;
}

static PyObject* py_load_ladspa_filter(PyObject* self, PyObject* args) {
    int channel;
    const char* filepath;
    const char* plugin_label;
    PyObject* controls_dict;
    

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "iss|O!", &channel, &filepath, &plugin_label,
        &PyDict_Type, &controls_dict)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    // setup controls values if present, these will initialize plugin
    if (gcsynth_channel_add_filter(channel, filepath, (char*) plugin_label) == -1) {
        return NULL;
    } 

    Py_RETURN_NONE;
}

static PyObject* py_gcsynth_noteon(PyObject* self, PyObject* args) {
    int channel;
    int midicode;
    int velocity;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "iii", &channel, &midicode, &velocity )) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    timing_log("py_gcsynth_noteon","noteon");
    gcsynth_noteon(&GcSynth, channel, midicode, velocity);

    Py_RETURN_NONE;
}

//int fluid_synth_program_select(fluid_synth_t *synth, int chan, int sfont_id,
//                               int bank_num, int preset_num);
static PyObject* py_fluid_synth_program_select(PyObject* self, PyObject* args) {
    int channel;
    int sfont_id;
    int bank_num;
    int preset_num;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "iiii", &channel, &sfont_id, &bank_num, &preset_num)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_select(&GcSynth, channel, sfont_id, bank_num, preset_num);
    
    Py_RETURN_NONE;

}

static PyObject* py_gcsynth_channel_set_control_by_name
    (PyObject* self, PyObject* args) {
    int channel;
    char* plugin_label;
    char* control_name;
    float value;


    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "issf", &channel, &plugin_label, &control_name, &value)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_channel_set_control_by_name(channel, plugin_label, 
        control_name, value);

    Py_RETURN_NONE;    
}


static PyObject* py_gcsynth_channel_set_control_by_index
    (PyObject* self, PyObject* args) {
    int channel;
    char* plugin_label;
    int control_num;
    float value;


    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "isif", &channel, &plugin_label, &control_num, &value)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)

    gcsynth_channel_set_control_by_index(channel, plugin_label, 
        control_num, value);

    Py_RETURN_NONE;    
}

static PyObject* py_gcsynth_noteoff(PyObject* self, PyObject* args) {
    int channel;
    int midicode;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "ii", &channel, &midicode)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)
    timing_log("py_gcsynth_noteoff","noteoff");
    gcsynth_noteoff(&GcSynth, channel, midicode);
    
    Py_RETURN_NONE;
}

static PyObject* py_fluid_synth_reset_basic_channel(PyObject* self, PyObject* args) {
    int channel;
    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "i", &channel)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)
    
    gcsynth_sequencer_remove_channel_events(&GcSynth, channel);

    Py_RETURN_NONE;
}

//int gcsynth_channel_remove_filter(int channel, char* plugin_label);
static PyObject* py_gcsynth_channel_remove_filter(PyObject* self, PyObject* args) {
    int channel;
    char* plugin_label_or_all = NULL; // if not specified remove all filters

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "i|s", &channel, &plugin_label_or_all)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    CHECK_CHANNEL_VALUE(channel)
    
    gcsynth_channel_remove_filter(channel, plugin_label_or_all);

    Py_RETURN_NONE;
}

static PyObject* py_gcsynth_sf_pitchrange(PyObject* self, PyObject* args) {
    int chan;
    float semitones;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "if", &chan, &semitones)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    gcsynth_sf_pitchrange(chan, semitones);
    Py_RETURN_NONE;
}

//gcsynth_sf_pitchwheel
static PyObject* py_gcsynth_sf_pitchwheel(PyObject* self, PyObject* args) {
    int chan;
    float semitones;

    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "if", &chan, &semitones)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    gcsynth_sf_pitchwheel(chan, semitones);
    Py_RETURN_NONE;
}


static PyObject* py_gcsynth_stop(PyObject* self, PyObject* args) {
    gcsynth_stop(&GcSynth);
    gcsynth_remove_all_filters();
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

    Py_RETURN_NONE; 
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
            //Py_XDECREF(pyItem);
        }
        //Py_XDECREF(py_list);
    } else {
        sprintf(errmsg,"start() command missing sfpaths or its not a list");
    }
    
}



static PyObject* py_ladspa_plugin_labels(PyObject* self, PyObject* args) {
    const char* filepath;
    
    // Parse the Python tuple, expecting two strings and a dictionary
    if (!PyArg_ParseTuple(args, "s", &filepath)) {
        return NULL;  // Return NULL to indicate an error if the parsing failed
    }

    return ladspa_get_labels(filepath);
}


// ------------ interface for moduler loader in python




// Define the methods of the module
static PyMethodDef GCSynthMethods[] = {
    {"stop", py_gcsynth_stop, METH_NOARGS, "Stop synth."},
    {"start", py_gcsynth_start, METH_VARARGS, "Start the gcsynth."},
    {"noteoff", py_gcsynth_noteoff,METH_VARARGS, "noteoff(chan,midicode)"},
    {"noteon", py_gcsynth_noteon,METH_VARARGS, "noteon(chan,midicod,velocity)"},
    {"select", py_fluid_synth_program_select, METH_VARARGS, "select(chan,sfont_id,bank,preset)"},
    
    {"ladspa_plugin_labels", py_ladspa_plugin_labels, METH_VARARGS, 
        "return a list of labels within a ladspa plugin"},
    {"filter_add",py_load_ladspa_filter, METH_VARARGS,"create a filter for a channel"},
    {"filter_remove",py_gcsynth_channel_remove_filter, METH_VARARGS,"remove filter from channel"},
    {"filter_query",py_query_filter, METH_VARARGS,"py_query_filter(path,plugin_label)->[{info}]"},

    {"filter_enable",py_gcsynth_channel_enable_filter, METH_VARARGS, "enable filter"},
    {"filter_disable",py_gcsynth_channel_disable_filter, METH_VARARGS, "disable filter"},
    {"pitchrange",py_gcsynth_sf_pitchrange, METH_VARARGS, "pitchrange(chan, semitones)"},
    {"pitchwheel",py_gcsynth_sf_pitchwheel, METH_VARARGS, "pitchwheel(chan, semitones)"},

    {"stop_capture",py_stop_capture,METH_NOARGS,"stop_capture() -> stops capture and audio thread"},
    {"start_capture",py_start_capture,METH_VARARGS,"start_capture(device) -> lanches capture and audio thread"},
    {"list_capture_devices",py_list_capture_devices,METH_VARARGS,"list_capture_devices() -> List[str]"},

    {"timer_event",py_gcsynth_event,METH_VARARGS,"send an event that gets executed in the future"},

    {"filter_set_control_by_name", py_gcsynth_channel_set_control_by_name, 
        METH_VARARGS,"filter_set_control_by_name(chan,plugin_label,name,value)" },


    {"filter_set_control_by_index", py_gcsynth_channel_set_control_by_index,
        METH_VARARGS,"filter_set_control_by_name(chan,plugin_label,index,value)" },

    {"channel_gain",py_channel_gain,METH_VARARGS,"channel_gain(chan,v) v = 0 no change"},
    {"reset_channel",py_fluid_synth_reset_basic_channel,METH_VARARGS,"reset_channel(chan)"},

    // aid in unit testing
    {"test_filter",py_filter_test,METH_VARARGS,"test_filter(path,plugin_label)-> pass or raise exception"},
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


/*
struct timespec start_time, end_time;

  // Get the start time
  clock_gettime(CLOCK_MONOTONIC, &start_time);

  // Perform some action
  // ... your code here ...

  // Get the end time
  clock_gettime(CLOCK_MONOTONIC, &end_time);

  // Calculate the time difference
  long seconds = end_time.tv_sec - start_time.tv_sec;
  long nanoseconds = end_time.tv_nsec - start_time.tv_nsec;

  // Handle potential negative nanoseconds (wrap around)
  if (nanoseconds < 0) {
    seconds--;
    nanoseconds += 1000000000;
  }

  printf("Elapsed time: %ld.%09ld seconds\n", seconds, nanoseconds);
*/
   
static FILE* TimingLog = NULL;
static struct timespec TimingLogRefTime;

void timing_log(char* caller, char *method)
{
    if (TimingLog != NULL) {
        struct timespec ts;
        long seconds;
        long nanoseconds;

        clock_gettime(CLOCK_MONOTONIC, &ts);

        seconds     = ts.tv_sec - TimingLogRefTime.tv_sec;
        nanoseconds = ts.tv_nsec - TimingLogRefTime.tv_nsec;

        if (nanoseconds < 0) {
            seconds--;
            nanoseconds += 1000000000;
        }
        
        fprintf(TimingLog,"%10ld.%09ld %12s %12s\n",
            seconds, nanoseconds, caller, method);
    }
}


// Initialization function
PyMODINIT_FUNC PyInit_gcsynth(void) {
    char* timing_log_env = getenv(TIMING_LOG_ENV);
 
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return NULL;
    }
    
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

    // add constants
    PyModule_AddIntConstant(module, "EV_NOTEON", EV_NOTEON);
    PyModule_AddIntConstant(module, "EV_NOTEOFF", EV_NOTEOFF);
    PyModule_AddIntConstant(module, "EV_FILTER_ADD", EV_FILTER_ADD);
    PyModule_AddIntConstant(module, "EV_FILTER_REMOVE", EV_FILTER_REMOVE);
    PyModule_AddIntConstant(module, "EV_FILTER_ENABLE", EV_FILTER_ENABLE);
    PyModule_AddIntConstant(module, "EV_FILTER_DISABLE", EV_FILTER_DISABLE);
    PyModule_AddIntConstant(module, "EV_FILTER_CONTROL", EV_FILTER_CONTROL);
    PyModule_AddIntConstant(module, "EV_PITCH_WHEEL", EV_PITCH_WHEEL);
    PyModule_AddIntConstant(module, "NUM_CHANNELS", NUM_CHANNELS); // max user specified channels
    PyModule_AddIntConstant(module, "LIVE_CAPTURE_CHANNEL", LIVE_CAPTURE_CHANNEL); // reserved for live capture

    if ((timing_log_env != NULL) && (strcmp(timing_log_env,"1") == 0)) {
        TimingLog = fopen(TIMING_LOGPATH,"w");
        int r = clock_gettime(CLOCK_MONOTONIC, &TimingLogRefTime);

        if (TimingLog == NULL) {
            fprintf(stderr,"Warning: %s was set but unable to create log!\n", TIMING_LOG_ENV);
        }
        if (r == -1) {
            fprintf(stderr,"Warning: unable to get monotonic clock! errno=%d %s\n", 
                errno, strerror(errno));
            fclose(TimingLog);
            TimingLog = NULL;    
        } 
    }


    
    return module;
}
