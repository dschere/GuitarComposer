#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>
#include <unistd.h> // For usleep()

#include "gcsynth.h"
#include "gcsynth_event.h"
#include "gcsynth_channel.h"
#include "gcsynth_sf.h"

#include <pthread.h>
#include <ev.h>
#include <glib.h>
#include <unistd.h>

struct timer_event_data {
    ev_timer timer_watcher; 
    struct scheduled_event* s_event;
};

struct gcsync_timer_dispatcher {
    GAsyncQueue *queue;
    struct ev_loop* loop;
    pthread_t thread;
    pthread_attr_t attr;
};


static struct gcsync_timer_dispatcher Dispatcher;

static int dispatcher_send(struct scheduled_event* s_event);
static void timer_callback(EV_P_ ev_timer *w, int revents);
static void *dispatcher_loop_thread(void *arg);
static int dispatcher_init();





static void timer_callback(EV_P_ ev_timer *w, int revents)
{
    struct timer_event_data* msg = (struct timer_event_data*) w->data;
    struct scheduled_event* s_event = msg->s_event;
    // switch on event

    // process scheduled events.
    switch(s_event->ev_type) {
        case EV_NOTEON:
            timing_log("timer_callback","noteon");
            gcsynth_sf_noteon(s_event->channel,
             s_event->midi_code, s_event->velocity);
            break;

        case EV_NOTEOFF:
            timing_log("timer_callback","noteoff");
            gcsynth_sf_noteoff(s_event->channel,
             s_event->midi_code);
            break;

        case EV_SELECT:
            gcsynth_sf_select(s_event->channel, s_event->sfont_id,
            s_event->bank_num, s_event->preset_num);   
            break;

        case EV_PITCH_WHEEL:
//printf("gcsynth_sf_pitchrange(%d,%f)\n", s_event->channel, s_event->pitch_change);
            gcsynth_sf_pitchwheel(s_event->channel, s_event->pitch_change);
            // todo
            break;

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

    // cleanup
    free(msg->s_event);
    free(msg);
}

/*
    service the libev loop for events.
*/
static void *dispatcher_loop_thread(void *arg)
{
    struct timer_event_data* msg;
    int usec_timeout = 5000;

    while (1) {
        msg = g_async_queue_timeout_pop(Dispatcher.queue, usec_timeout);
        if (msg) {
            msg->timer_watcher.data = msg; // circular ref needed for cleanup
            ev_timer_init(&msg->timer_watcher,timer_callback,
                msg->s_event->when * 0.001, 0.0);
            // call timer_callback in 'when' milliseconds.    
            ev_timer_start(Dispatcher.loop, &msg->timer_watcher);    
        } 

        // process any libev events without waiting for future ones.
        ev_loop(Dispatcher.loop, EVLOOP_NONBLOCK);
    }

    ev_loop_destroy(Dispatcher.loop);
    return NULL;
}




/* 
    route scheduled event to dispatch thread.
*/
static int dispatcher_send(struct scheduled_event* s_event)
{
    int err = 0;
    struct timer_event_data* msg = (struct timer_event_data*)
        calloc(1, sizeof(struct timer_event_data));

    if (!msg) {
        fprintf(stderr,
            "dispatcher_send: Unable to allocate memory\n");
        err = -1;
    } else {
        msg->s_event = s_event;
        msg->timer_watcher.data = msg;
        // enqueue
        g_async_queue_push(Dispatcher.queue, msg);
    }

    return err;
}


//TODO
/**
 * Need a function that can skip forwards or backwards, that is
 * alter the time of timer being fired while inflight. This
 * can be done be keeping a table of all inflight events and the 
 * creation time.
 * 
 * skip ahead ->
 *  compute the elapsed time (now+skip) and search through all inflight timers
 *  if elapsed > when delete the timer, otherwise delete and reschedule 
 *  at a new time
 * 
 * skip backwards -> 
 *  this must be done by the caller, provide a way to delete all inflight
 *  events. then schedule events.
 * 
 */



/*
    A thread is used to aid libev in launching timer events, its purpose is
    to service an async queue that will kick off events to be executed 
    in teh future.
*/
static int dispatcher_init()
{
    Dispatcher.loop = ev_loop_new(EVFLAG_AUTO);
    if (Dispatcher.loop == NULL) {
        fprintf(stderr,"gcsynth_event: ev_loop_new failed!\n");
        return -1;
    }

    pthread_attr_init(&Dispatcher.attr);
    pthread_attr_setdetachstate(&Dispatcher.attr, PTHREAD_CREATE_DETACHED); // Daemon thread

    // Initialize GLib async queue
    Dispatcher.queue = g_async_queue_new();

    if (pthread_create(
        &Dispatcher.thread, 
        &Dispatcher.attr, dispatcher_loop_thread, NULL) != 0) {
        fprintf(stderr, "Failed to create thread\n");
        return -1;
    }

    pthread_attr_destroy(&Dispatcher.attr);
    
    return 0;
}


void gcsynth_noteon(struct gcsynth* gcs, int chan, int midicode, int velocity)
{
    if (gcsynth_sf_noteon(chan, midicode, velocity) == -1) {
         gcsynth_raise_exception("gcsynth_sf_noteon");
    }
}


void gcsynth_noteoff(struct gcsynth* gcs, int chan, int midicode)
{
    if (gcsynth_sf_noteoff(chan, midicode) == -1) {
        gcsynth_raise_exception("gcsynth_sf_noteoff");
    }
}

void gcsynth_select(struct gcsynth* gcs, int chan,  int sfont_id, int bank_num, int preset_num)
{
    if (gcsynth_sf_select(chan, sfont_id,bank_num, preset_num) == -1) {
        gcsynth_raise_exception("gcsynth_sf_select");
    }
}


void gcsynth_schedule(struct gcsynth* gcs, struct scheduled_event* s_event)
{
     if (dispatcher_send(s_event) == -1) {
        gcsynth_raise_exception("gcsynth_schedule");
     }
}


void gcsynth_sequencer_remove_channel_events(struct gcsynth* gcs, int chan)
{
    // todo?
}


void gcsynth_sequencer_setup(struct gcsynth* gcs)
{
    dispatcher_init();                            
}
