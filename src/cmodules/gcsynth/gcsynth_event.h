#ifndef __GCSYNTH_EVENT_H
#define __GCSYNTH_EVENT_H

#include "gcsynth.h"

enum GCSYNTH_EVENT {

    // events specific to gcsynth
    EV_FILTER_ADD,
    EV_FILTER_REMOVE,
    EV_FILTER_ENABLE,
    EV_FILTER_DISABLE,
    EV_FILTER_CONTROL,

    EV_FLUID_SYNTH_EVENTS, // values above this are 
                           // fluid synth events
    EV_NOTEON,
    EV_NOTEOFF,
    EV_SELECT,
    EV_PITCH_WHEEL,

    EV_NUM_EVENTS
};

#define EV_NULL_EVENT -1

struct scheduled_event {
    unsigned int when;
    int channel;
    int ev_type;
    
    int midi_code;
    int velocity;

    int sfont_id;
    int bank_num;
    int preset_num;

    const char* plugin_label;
    const char* plugin_path;
    int   enable;
    const char* control_name;
    int   control_index;
    float control_value;

    float pitch_change; // in half steps
 
    int event_id;
    struct gcsynth* gcs;
    // used to ensure that there was not a stop/start
    // event while the timer was sleeping
    int gcsynth_inst_id_when_timer_started; 
};

// scheduled event execution
void gcsynth_schedule(struct gcsynth* gcs, struct scheduled_event* event);

// immediate execution of synth events
void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity, int gstring);
void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode, int gstring);
void gcsynth_select(struct gcsynth* gcs, int chan,  int sfont_id, int bank_num, int preset_num);


void gcsynth_sequencer_setup(struct gcsynth* gcs);
void gcsynth_sequencer_remove_channel_events(struct gcsynth* gcs, int chan);




#endif