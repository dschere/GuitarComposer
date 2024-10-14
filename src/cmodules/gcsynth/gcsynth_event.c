#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>
#include <unistd.h> // For usleep()

#include "gcsynth_event.h"
#include "gcsynth_channel.h"




static void gcsynth_schedule_fluidsynth_event(struct gcsynth* gcs, 
    struct scheduled_event* s_event);
static void gcsynth_schedule_custom_event(struct gcsynth* gcs, 
    struct scheduled_event* s_event);
//static void* thread_timer_function(void* arg);    


void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity)
{
    fluid_synth_noteon(gcs->synth, chan, midicode, velocity);
}


void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode)
{
    fluid_synth_noteoff(gcs->synth, chan, midicode);
}

void gcsynth_select(struct gcsynth* gcs, int chan,  int sfont_id, int bank_num, int preset_num)
{
    fluid_synth_program_select(gcs->synth, chan, sfont_id, bank_num, preset_num);
}


void gcsynth_schedule(struct gcsynth* gcs, struct scheduled_event* s_event)
{
    if (s_event->ev_type > EV_FLUID_SYNTH_EVENTS) {
        gcsynth_schedule_fluidsynth_event(gcs, s_event);
        free(s_event);
    } else {
        gcsynth_schedule_custom_event(gcs, s_event);
        // freed inside timer callback.
    }
}

static void timer_function(void* arg)
{
    struct scheduled_event* s_event = (struct scheduled_event*) arg;
    struct gcsynth_active_state state;
    long milliseconds = (long) s_event->when;
    struct timespec ts;

    ts.tv_sec = milliseconds / 1000; // Convert milliseconds to seconds
    ts.tv_nsec = (milliseconds % 1000) * 1000000;

    if (nanosleep(&ts, NULL) < 0) {
        goto exit_timer_callback;
    }

    // determine if the synth is not running, or if a restart
    // occured while we were asleep, in either case discard this event.
    state = gcsynth_get_active_state();
    if ((state.running == 0) || 
        (state.instance_id != s_event->gcsynth_inst_id_when_timer_started)) {
        goto exit_timer_callback;              
    }  

    switch(s_event->ev_type) {
        case EV_FILTER_ADD:
            gcsynth_channel_add_filter(
            s_event->channel, 
        s_event->plugin_path, 
        (char *) s_event->plugin_label
            );                        
            break;
        case EV_FILTER_CONTROL:
            if (s_event->control_name == NULL) { 
                gcsynth_channel_set_control_by_index(
                    s_event->channel,
                    (char *) s_event->plugin_label,
                    s_event->control_index,
                    s_event->control_value
                );
            } else {
                gcsynth_channel_set_control_by_name(
                    s_event->channel,
                    (char *) s_event->plugin_label,
                    (char *) s_event->control_name,
                    s_event->control_value
                );
            }
            break;
        case EV_FILTER_ENABLE:
            gcsynth_channel_enable_filter(s_event->channel, 
                (char *) s_event->plugin_label);
            break;
        case EV_FILTER_DISABLE:
            gcsynth_channel_disable_filter(s_event->channel, 
                (char *) s_event->plugin_label);
            break;        
    }
    
exit_timer_callback:

    free(s_event);
}


static void gcsynth_schedule_custom_event(struct gcsynth* gcs, 
    struct scheduled_event* s_event)
{
    fluid_event_t *ev = new_fluid_event();
    fluid_event_set_source(ev, -1);
    fluid_event_set_dest(ev, gcs->synth_destination);
    fluid_event_timer(ev, s_event, timer_function);
    fluid_sequencer_send_at(gcs->sequencer, ev, s_event->when, 0);
    delete_fluid_event(ev);
}

#define PITCH_WHEEL_MIDRANGE 8192

static void gcsynth_schedule_fluidsynth_event(struct gcsynth* gcs, 
    struct scheduled_event* s_event)
{
    fluid_event_t *ev = new_fluid_event();
    fluid_event_set_source(ev, -1);
    fluid_event_set_dest(ev, gcs->synth_destination);
    int pitch;

    switch(s_event->ev_type) { 
        case EV_NOTEON:
            fluid_event_noteon(ev, s_event->channel, 
                s_event->midi_code, s_event->velocity);
            break;
        case EV_NOTEOFF:
            fluid_event_noteoff(ev, s_event->channel, s_event->midi_code);
            break;
        case EV_SELECT:
            fluid_event_program_select(ev, s_event->channel, 
                 s_event->sfont_id, s_event->bank_num, 
                 s_event->preset_num);
            break;    
        case EV_PITCH_WHEEL:
            //	MIDI pitch bend value (0-16383, 8192 = no bend)
            pitch = (int) PITCH_WHEEL_MIDRANGE + (s_event->pitch_change/PITCH_WHEEL_SENSITIVITY);
            if (pitch < 0)     pitch = 0;
            if (pitch > 16383) pitch = 16383;
            fluid_event_pitch_bend(ev, s_event->channel, pitch);    
            break;
        
    }

    fluid_sequencer_send_at(gcs->sequencer, ev, s_event->when, 0);
    delete_fluid_event(ev);
        
}

/*
TODO WE ARE LIMITED TO 825 THREADS.

must use fluid synth's timer. 

should allow for user data to be attached to the fluid_synth_event 


*/

void gcsynth_sequencer_setup(struct gcsynth* gcs)
{
    gcs->sequencer = new_fluid_sequencer2(0);
            
    /* register the synth with the sequencer */
    gcs->synth_destination = fluid_sequencer_register_fluidsynth(gcs->sequencer,
                                gcs->synth);
}
