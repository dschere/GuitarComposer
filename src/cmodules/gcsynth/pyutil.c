#include <dlfcn.h>
#include <Python.h>

#include "pyutil.h"
#include "ladspa.h"

void raise_value_error(char *msg) {
    // Raise a ValueError with a custom message
    PyErr_SetString(PyExc_ValueError, msg);
}


const char *get_dict_str_field(PyObject* dict, const char* key, const char* defval)
{
    PyObject* dict_field = NULL;
    PyObject* py_str = NULL;
    char* result = NULL;

    // Get the value from the dictionary (borrowed reference)
    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        // Convert the value to a UTF-8 encoded bytes object (new reference)
        if ((py_str = PyUnicode_AsUTF8String(dict_field)) != NULL) {
            // Get the C string from the bytes object (borrowed pointer)
            const char* temp_value = PyBytes_AsString(py_str);
            if (temp_value != NULL) {
                // Duplicate the string to return to the caller
                result = strdup(temp_value);
            }
            // Clean up the bytes object
            Py_DECREF(py_str);
        }
    }

    // If no value was found, duplicate the default value (if provided)
    if (result == NULL && defval != NULL) {
        result = strdup(defval);
    }

    return result;  // Caller must free this memory
}

long get_dict_int_field(PyObject* dict, const char*key, long defval)
{
    PyObject* dict_field = NULL;
    long result = defval;

    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        result = PyLong_AsLong(dict_field);
        //Py_DECREF(dict_field);
    }

    return result;     
}

float get_dict_flt_field(PyObject* dict, const char*key, float defval)
{
    PyObject* dict_field = NULL;
    float result = defval;

    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        result = (float) PyFloat_AsDouble(dict_field);
        //Py_DECREF(dict_field);
    }

    return result;     
}

/*
struct scheduled_event {
    unsigned int when;
    int channel;
    int ev_type;
    
    int midi_code;
    int velocity;

    char* plugin_name;
    char* plugin_path;
    int   enable;
    char* control_name;
    int   control_index;
    float control_value;

    float pitch_change; // in half steps
 
    int event_id;
};

*/
static unsigned long EventIdCounter = 0;

static void print_event(struct scheduled_event* ev) {
    printf("scheduled_event:\n");
    if (ev) {
        printf("\nev_type = %d, ev_channel = %d, when=%d \n",
            ev->ev_type, ev->channel, ev->when
        ); 
    } else {
        printf("null\n");
    }
}

struct scheduled_event* event_from_pydata(PyObject* dict)
{
    struct scheduled_event* ev = (struct scheduled_event*)
        calloc(1,sizeof(struct scheduled_event));
    char* errmsg = NULL;    

    if (ev) {
        ev->ev_type = get_dict_int_field(dict,"ev_type",-1);        
        if ((ev->channel = get_dict_int_field(dict,"channel",-1)) == -1) {
            errmsg = "event_from_pydata: channel is required ";    
        }
        ev->when = get_dict_int_field(dict,"when", 0);
        ev->event_id = EventIdCounter++;

        switch(ev->ev_type)
        {
            case EV_NOTEON:
                if ((ev->velocity = 
                    get_dict_int_field(dict,"velocity",-1)) == -1) {
                    errmsg = 
                        "event_from_pydata: velocity missing for noteon event";
                }
                if ((ev->midi_code = 
                    get_dict_int_field(dict,"midi_code",-1)) == -1) {
                    errmsg = "event_from_pydata: midi_code is missing.";
                }
                break;

            case EV_NOTEOFF:
                if ((ev->midi_code = 
                    get_dict_int_field(dict,"midi_code",-1)) == -1) {
                    errmsg = "event_from_pydata: midi_code is missing.";
                }
                break;

            case EV_FILTER_ADD:
                if ((ev->plugin_path = 
                    get_dict_str_field(dict,"plugin_path",NULL)) == NULL) {
                    errmsg = "event_from_pydata: plugin_path is missing";
                }
                else if ((ev->plugin_label = 
                    get_dict_str_field(dict,"plugin_label",NULL)) == NULL) {
                    errmsg = "event_from_pydata: plugin_label is missing";
                }  
                break;

            case EV_FILTER_ENABLE:
                ev->enable = 1;
                if ((ev->plugin_label = 
                    get_dict_str_field(dict,"plugin_label",NULL)) == NULL) {
                    errmsg = "event_from_pydata: plugin_label is missing";
                }  
                break;

            case EV_FILTER_DISABLE:
                ev->enable = 0;
                if ((ev->plugin_label = 
                    get_dict_str_field(dict,"plugin_label",NULL)) == NULL) {
                    errmsg = "event_from_pydata: plugin_label is missing";
                }  
                break;

            case EV_FILTER_CONTROL:
                ev->control_name = get_dict_str_field(dict,"control_name",NULL);
                ev->control_index = get_dict_int_field(dict, "control_index", -1);
                if ((ev->control_index == -1) && (ev->control_name == NULL)) {
                    errmsg = "event_from_pydata: either control name/index must be defined";
                } else if ((ev->plugin_label = 
                    get_dict_str_field(dict,"plugin_label",NULL)) == NULL) {
                    errmsg = "event_from_pydata: plugin_label is missing";
                } else {
                    ev->control_value = get_dict_flt_field(dict,"control_value",0.0);
                }
                break;

            case EV_SELECT:
                ev->sfont_id = get_dict_int_field(dict,"sfont_id",0);
                ev->bank_num = get_dict_int_field(dict,"bank_num",0);
                ev->preset_num = get_dict_int_field(dict,"preset_num",0);
                break;

            case EV_PITCH_WHEEL:
                ev->pitch_change = get_dict_flt_field(dict,"pitch_change",0.0);
                break;      

            default:
                errmsg = "event_from_pydata: Invalid type";
                break;
        }
    }

    // handle errors
    if (errmsg) {
        print_event(ev);
        gcsynth_raise_exception(errmsg);
        if (ev) {
            free(ev);
            ev = NULL;
        }
    }

    return ev;
}



PyObject* ladspa_get_labels(const char* path) {
    int i;
    void* dl_handle = dlopen(path, RTLD_LOCAL|RTLD_NOW);
    PyObject* labels = PyList_New(0);

    if ((dl_handle != NULL) && (labels != NULL)) {
        LADSPA_Descriptor_Function descriptor_fn = 
            dlsym(dl_handle, "ladspa_descriptor");

        if (descriptor_fn) {
            LADSPA_Descriptor *desc;
            for (i = 0; ((desc = (LADSPA_Descriptor *)descriptor_fn(i)) != NULL); i++) {
                char data[4096];
                
                sprintf(data,"%s:%s", desc->Label, desc->Name);
                PyObject* py_str = PyUnicode_FromString(data);
                if (!py_str) {
                    Py_DECREF(labels); // Clean up list on error
                    return NULL;
                }
        
                // Append string to list
                if (PyList_Append(labels, py_str) < 0) {
                    Py_DECREF(py_str); // Clean up string
                    Py_DECREF(labels);  // Clean up list
                    return NULL;
                }
                Py_DECREF(py_str); // List takes ownership, so release reference
            }
        }
        dlclose(dl_handle);
    }

    return labels;
}