#ifndef __PYUTIL_H__
#define __PYUTIL_H__

#include <Python.h>

#include "gcsynth_event.h"

const char *get_dict_str_field(PyObject* dict, const char*key, const char* defval);
long        get_dict_int_field(PyObject* dict, const char*key, long defval);
float       get_dict_flt_field(PyObject* dict, const char*key, float defval);

struct scheduled_event* event_from_pydata(PyObject* dict);

void raise_value_error(char* msg);

PyObject* ladspa_get_labels(const char* path);

#endif