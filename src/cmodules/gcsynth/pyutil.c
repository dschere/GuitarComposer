#include <Python.h>

#include "pyutil.h"

void raise_value_error(char *msg) {
    // Raise a ValueError with a custom message
    PyErr_SetString(PyExc_ValueError, msg);
}

const char *get_dict_str_field(PyObject* dict, const char*key, const char* defval)
{
    PyObject* dict_field = NULL;
    PyObject* py_str = NULL;
    const char* value = defval;

    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        if ((py_str = PyUnicode_AsUTF8String(dict_field)) != NULL) {
            value = PyBytes_AsString(py_str);
        }
    }

    if (value) {
        value = strdup(value);
    }

    if (dict_field) {
        Py_DECREF(dict_field);
    }
    if (py_str) {
        Py_DECREF(py_str);
    }

    return value;
}

long get_dict_int_field(PyObject* dict, const char*key, long defval)
{
    PyObject* dict_field = NULL;
    long result = defval;

    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        result = PyLong_AsLong(dict_field);
        Py_DECREF(dict_field);
    }

    return result;     
}

float get_dict_flt_field(PyObject* dict, const char*key, float defval)
{
    PyObject* dict_field = NULL;
    float result = defval;

    if ((dict_field = PyDict_GetItemString(dict, key)) != NULL) {
        result = (float) PyFloat_AsDouble(dict_field);
        Py_DECREF(dict_field);
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
        gcsynth_raise_exception(errmsg);
        if (ev) {
            free(ev);
            ev = NULL;
        }
    }

    return ev;
}
